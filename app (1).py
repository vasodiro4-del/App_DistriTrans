
import math
import subprocess
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Logística 5D - PoC v2", page_icon="🚚", layout="wide")
RNG = np.random.default_rng(42)

# ---------- Datos ----------
def initial_data():
    d = date.today()
    customers = []
    windows = [("08:00","11:00"),("09:00","13:00"),("10:00","14:00"),
               ("11:00","15:00"),("13:00","17:00")]
    for i in range(1, 16):
        a, b = windows[(i-1) % len(windows)]
        customers.append({
            "cliente_id": f"C-{i:02d}", "cliente": f"Cliente {i:02d}",
            "x": round(float(RNG.uniform(2, 30)), 2),
            "y": round(float(RNG.uniform(2, 25)), 2),
            "demanda_kg": int(RNG.integers(250, 1800)),
            "ventana_inicio": a, "ventana_fin": b,
            "servicio_min": int(RNG.integers(10, 25))
        })
    customers = pd.DataFrame(customers)

    inventory = pd.DataFrame([
        ["SKU-001","Producto terminado A",850,"A-01",250,"Cajas"],
        ["SKU-002","Producto terminado B",620,"A-02",200,"Cajas"],
        ["SKU-003","Producto terminado C",430,"B-01",150,"Unidades"],
        ["SKU-004","Producto terminado D",310,"B-02",100,"Paquetes"],
        ["SKU-005","Producto terminado E",980,"C-01",300,"Cajas"],
        ["SKU-006","Producto terminado F",540,"C-02",180,"Unidades"],
    ], columns=["SKU","Descripción","Stock","ubicación","stock mínimo","Unidad"])
    inventory["estado"] = np.where(inventory["Stock"] <= inventory["stock mínimo"], "Bajo", "Óptimo")

    entradas = pd.DataFrame([
        [d-timedelta(days=4),"GUIA-IN-001","SKU-001","Producto terminado A",200,"Cajas","Optimo"],
        [d-timedelta(days=3),"GUIA-IN-002","SKU-003","Producto terminado C",120,"Unidades","Con daños"],
        [d-timedelta(days=2),"GUIA-IN-003","SKU-005","Producto terminado E",300,"Cajas","Optimo"],
    ], columns=["fecha","#guia envío","sku","descripción","cantidad","unidad de medida","estado"])

    salidas = pd.DataFrame([
        ["GUIA-OUT-001","SKU-001","Producto terminado A",90,"Empacado",d-timedelta(days=2)],
        ["GUIA-OUT-002","SKU-005","Producto terminado E",140,"Enviado",d-timedelta(days=1)],
        ["GUIA-OUT-003","SKU-002","Producto terminado B",80,"Empacado",d],
    ], columns=["#guia despacho","sku","descripción","cantidad","estado","fecha de picking"])

    carga = pd.DataFrame([
        ["GUIA-OUT-001","Almacén Central → Cliente 01",900,8.5,"ABC-123","Transportes Caribe",d,d+timedelta(days=1),420000,"En tránsito"],
        ["GUIA-OUT-002","Almacén Central → Cliente 05",1500,14.0,"DEF-456","Logística Norte",d,d+timedelta(days=1),610000,"Listo para despacho"],
        ["GUIA-OUT-003","Almacén Central → Cliente 02",650,6.0,"GHI-789","Transportes Caribe",d-timedelta(days=1),d,330000,"Recibido"],
    ], columns=["#guia","origen destino","peso","volumen","flota","transportista",
                "fecha de salida","fecha de entrega estimada","costo","estado"])

    flota = pd.DataFrame([
        ["ABC-123","Camión liviano",3500,18,48200,7.8,d+timedelta(days=12),"Disponible"],
        ["DEF-456","Camión mediano",7000,30,73600,6.5,d+timedelta(days=5),"En tránsito"],
        ["GHI-789","Camión mediano",6500,28,55100,6.9,d+timedelta(days=2),"Disponible"],
        ["JKL-321","Camión pesado",10000,45,91200,5.2,d+timedelta(days=1),"Mantenimiento"],
        ["MNO-654","Van",1800,12,32100,9.5,d+timedelta(days=25),"Disponible"],
    ], columns=["placa","vehículo","capacidad peso (kg)","capacidad volumen (m3)",
                "kilometraje","consumo gasolina (km/L)","mantenimiento próximo","estado"])

    historial = pd.DataFrame([
        [d-timedelta(days=7),"GUIA-OUT-001","ABC-123","Camión liviano","Carlos Pérez"],
        [d-timedelta(days=5),"GUIA-OUT-002","DEF-456","Camión mediano","Laura Gómez"],
        [d-timedelta(days=2),"GUIA-OUT-003","GHI-789","Camión mediano","Andrés Ruiz"],
    ], columns=["fecha","#guia","placa","vehículo","conductor asignado"])

    documentos = pd.DataFrame([
        ["ABC-123","Camión liviano","2026-11-15","2026-10-20","2026-12-01"],
        ["DEF-456","Camión mediano","2026-09-10","2026-09-25","2026-12-20"],
        ["GHI-789","Camión mediano","2026-12-05","2026-11-11","2026-10-30"],
        ["JKL-321","Camión pesado","2026-08-30","2026-09-01","2026-11-15"],
        ["MNO-654","Van","2027-01-10","2026-12-15","2027-01-20"],
    ], columns=["placa","vehículo","SOAT","revisión tecnomecánica","seguros"])

    aduanas = pd.DataFrame([
        ["GUIA-IMP-001","Colombia","China","Maquinaria","8479.89",12000,5.0,
         "Factura, lista empaque, origen","Completo","Aprobado"],
        ["GUIA-IMP-002","Colombia","México","Repuestos","8708.99",8000,10.0,
         "Factura, lista empaque","Incompleto","Pendiente"],
        ["GUIA-EXP-003","Colombia","Panamá","Producto terminado","1905.90",6500,15.0,
         "Factura, origen, sanitario","Completo","Aprobado"],
    ], columns=["#trámite","destino","origen","mercancía","partida arancelaria",
                "valor CIF","arancel %","documentos requeridos","documentación","estado"])
    return customers, inventory, entradas, salidas, carga, flota, historial, documentos, aduanas

if "init" not in st.session_state:
    names = ["customers","inventory","entradas","salidas","carga","flota","historial","documentos","aduanas"]
    for n, df in zip(names, initial_data()):
        st.session_state[n] = df
    st.session_state.init = True

def mins(s):
    try:
        h,m = map(int, str(s).split(":")[:2]); return h*60+m
    except Exception: return 0

def vrp_nn(df, nveh, cap, speed, maxkm):
    remaining = set(df.index)
    routes = []
    for v in range(1, nveh+1):
        if not remaining: break
        x=y=0.0; t=480; load=dist=0.0; stops=[]
        while remaining:
            candidates=[]
            for i in remaining:
                r=df.loc[i]; dd=math.hypot(r.x-x,r.y-y)
                arr=t+dd/max(speed,1)*60
                start,end=mins(r.ventana_inicio),mins(r.ventana_fin)
                service=max(arr,start)
                if load+r.demanda_kg<=cap and dist+dd<=maxkm and service<=end:
                    candidates.append((dd,i,arr,service,max(0,start-arr)))
            if not candidates: break
            dd,i,arr,service,wait=min(candidates,key=lambda z:(z[0],z[4]))
            r=df.loc[i]
            dist += dd; load += r.demanda_kg; t=service+r.servicio_min
            x,y=float(r.x),float(r.y)
            stops.append({"cliente":r.cliente,"x":r.x,"y":r.y,"demanda_kg":r.demanda_kg,
                          "ventana":f"{r.ventana_inicio}-{r.ventana_fin}",
                          "llegada_min":round(arr,1),"espera_min":round(wait,1)})
            remaining.remove(i)
        if stops:
            dist += math.hypot(x,y)
            routes.append({"ruta":f"Ruta-{v}","distancia_km":round(dist,2),
                           "carga_kg":round(load,1),"paradas":stops})
    return routes, remaining

def inventory_projection(df, days):
    rows=[]
    for _,r in df.iterrows():
        stock=float(r.Stock); minimum=float(r["stock mínimo"])
        daily=max(1.0,minimum/7)
        projected=max(0,stock-daily*days)
        days_min=max(0,int((stock-minimum)/daily)) if stock>minimum else 0
        rows.append([r.SKU,r.Descripción,stock,round(daily,1),round(projected,1),days_min])
    return pd.DataFrame(rows,columns=["SKU","Descripción","Stock actual",
                                      "Demanda diaria estimada","Stock proyectado",
                                      "Días hasta stock mínimo"])

def maintenance_risk(r):
    dt=pd.to_datetime(r["mantenimiento próximo"],errors="coerce")
    days=(dt.date()-date.today()).days if pd.notna(dt) else 999
    risk=50 if days<=7 else 25 if days<=30 else 0
    km=float(r.kilometraje); cons=float(r["consumo gasolina (km/L)"])
    risk += 30 if km>=80000 else 15 if km>=50000 else 0
    risk += 20 if cons<6 else 0
    return min(risk,100)

def freight_optimize(carga, flota):
    available=flota[flota.estado.astype(str).str.lower()=="disponible"]
    if available.empty: available=flota
    out=carga.copy(); plates=[]; costs=[]
    for _,r in out.iterrows():
        cand=available[(available["capacidad peso (kg)"]>=float(r.peso)) &
                       (available["capacidad volumen (m3)"]>=float(r.volumen))]
        if cand.empty: cand=available
        chosen=cand.iloc[0]
        plates.append(chosen.placa)
        costs.append(round(float(r.costo)+max(0,float(r.peso)-1000)*50+
                           max(0,float(r.volumen)-10)*3000,0))
    out["flota sugerida"]=plates; out["costo optimizado"]=costs
    return out

# ---------- UI ----------
st.title("🚚 Logística 5D — Proof of Concept v2")
st.caption("Distribución y Transporte · datos sintéticos · sesión temporal")

with st.sidebar:
    st.header("Parámetros")
    fuel=st.slider("Gasolina (COP/L)",8000,20000,15000,500)
    km_cost=st.slider("Costo logístico por km (COP)",500,5000,2500,100)
    target=st.slider("Nivel de servicio objetivo (%)",80,100,95,1)
    st.divider()
    st.success("✓ Streamlit está activo")

T=st.tabs(["🚛 Transporte","🏭 Almacenes","📦 Carga","🚗 Flotas","🛃 Aduanas"])

with T[0]:
    st.header("Gestión de Transporte")
    a,b,c,d=st.columns(4)
    n=a.slider("Vehículos",1,10,4); cap=b.slider("Capacidad/vehículo (kg)",1000,15000,5000,500)
    speed=c.slider("Velocidad (km/h)",20,80,35,5); maxkm=d.slider("Máximo km/ruta",50,300,150,10)
    routes,unserved=vrp_nn(st.session_state.customers,n,cap,speed,maxkm)
    total_km=sum(r["distancia_km"] for r in routes); served=len(st.session_state.customers)-len(unserved)
    service=served/len(st.session_state.customers)*100; load=sum(r["carga_kg"] for r in routes)
    cost=total_km*km_cost+(total_km/7)*fuel
    m1,m2,m3,m4,m5=st.columns(5)
    m1.metric("Distancia",f"{total_km:.1f} km"); m2.metric("Carga",f"{load:,.0f} kg")
    m3.metric("Atendidos",f"{served}/{len(st.session_state.customers)}")
    m4.metric("Servicio",f"{service:.1f}%"); m5.metric("Costo",f"${cost:,.0f}")
    if service<target: st.warning("Nivel de servicio inferior al objetivo.")
    if unserved: st.warning(f"{len(unserved)} clientes sin asignar.")
    if routes:
        pts=[]
        for r in routes:
            pts.append({"ruta":r["ruta"],"x":0,"y":0,"punto":"Almacén"})
            pts += [{"ruta":r["ruta"],"x":p["x"],"y":p["y"],"punto":p["cliente"]} for p in r["paradas"]]
        st.plotly_chart(px.line(pd.DataFrame(pts),x="x",y="y",color="ruta",markers=True,
                                hover_name="punto",title="Rutas propuestas"),use_container_width=True)
        st.dataframe(pd.DataFrame([[r["ruta"],r["distancia_km"],r["carga_kg"],len(r["paradas"])] for r in routes],
                                  columns=["Ruta","Distancia km","Carga kg","Paradas"]),use_container_width=True)

with T[1]:
    st.header("Gestión de Almacenes")
    S=st.tabs(["Inventario","Entradas","Salidas","Proyección"])
    with S[0]:
        e=st.data_editor(st.session_state.inventory,num_rows="dynamic",use_container_width=True,key="inv")
        if st.button("Guardar inventario"): st.session_state.inventory=e.copy(); st.success("Guardado.")
        st.plotly_chart(px.bar(st.session_state.inventory,x="SKU",y="Stock",color="estado",
                                title="Stock por SKU"),use_container_width=True)
    with S[1]:
        e=st.data_editor(st.session_state.entradas,num_rows="dynamic",use_container_width=True,key="in")
        if st.button("Guardar entradas"): st.session_state.entradas=e.copy(); st.success("Guardado.")
    with S[2]:
        e=st.data_editor(st.session_state.salidas,num_rows="dynamic",use_container_width=True,key="out")
        if st.button("Guardar salidas"): st.session_state.salidas=e.copy(); st.success("Guardado.")
    with S[3]:
        days=st.slider("Horizonte (días)",7,90,30)
        p=inventory_projection(st.session_state.inventory,days)
        st.dataframe(p,use_container_width=True)
        st.plotly_chart(px.bar(p,x="SKU",y=["Stock actual","Stock proyectado"],barmode="group",
                               title=f"Proyección a {days} días"),use_container_width=True)

with T[2]:
    st.header("Gestión de Carga")
    e=st.data_editor(st.session_state.carga,num_rows="dynamic",use_container_width=True,key="freight")
    if st.button("Guardar carga"): st.session_state.carga=e.copy(); st.success("Guardado.")
    opt=freight_optimize(st.session_state.carga,st.session_state.flota)
    st.dataframe(opt,use_container_width=True)
    if not opt.empty:
        st.metric("Costo optimizado total",f"${pd.to_numeric(opt['costo optimizado']).sum():,.0f}")
        st.plotly_chart(px.bar(opt,x="#guia",y="costo optimizado",color="estado",
                               title="Costo por guía"),use_container_width=True)

with T[3]:
    st.header("Gestión de Flotas")
    S=st.tabs(["Inventario","Historial","Documentación"])
    with S[0]:
        e=st.data_editor(st.session_state.flota,num_rows="dynamic",use_container_width=True,key="fleet")
        if st.button("Guardar flota"): st.session_state.flota=e.copy(); st.success("Guardado.")
        r=st.session_state.flota.copy(); r["riesgo mantenimiento (%)"]=r.apply(maintenance_risk,axis=1)
        st.plotly_chart(px.bar(r,x="placa",y="riesgo mantenimiento (%)",color="estado",
                               title="Riesgo de mantenimiento"),use_container_width=True)
    with S[1]:
        e=st.data_editor(st.session_state.historial,num_rows="dynamic",use_container_width=True,key="hist")
        if st.button("Guardar historial"): st.session_state.historial=e.copy(); st.success("Guardado.")
        with st.form("driver"):
            driver=st.text_input("Nuevo conductor")
            plate=st.selectbox("Placa",st.session_state.flota.placa.astype(str))
            if st.form_submit_button("Agregar conductor") and driver.strip():
                vehicle=st.session_state.flota.loc[st.session_state.flota.placa.astype(str)==plate,"vehículo"].iloc[0]
                row=pd.DataFrame([[date.today(),"PENDIENTE",plate,vehicle,driver.strip()]],
                                 columns=st.session_state.historial.columns)
                st.session_state.historial=pd.concat([st.session_state.historial,row],ignore_index=True)
                st.success("Conductor agregado.")
    with S[2]:
        e=st.data_editor(st.session_state.documentos,num_rows="dynamic",use_container_width=True,key="docs")
        if st.button("Guardar documentación"): st.session_state.documentos=e.copy(); st.success("Guardado.")
        doc=st.session_state.documentos.copy()
        today=pd.Timestamp(date.today())
        date_cols=["SOAT","revisión tecnomecánica","seguros"]
        parsed=doc[date_cols].apply(pd.to_datetime,errors="coerce")
        doc["días al vencimiento"]=(parsed.min(axis=1)-today).dt.days
        st.dataframe(doc,use_container_width=True)
        if (doc["días al vencimiento"]<=30).any(): st.warning("Hay documentos vencidos o próximos a vencer.")

with T[4]:
    st.header("Gestión Aduanera / Trámites")
    e=st.data_editor(st.session_state.aduanas,num_rows="dynamic",use_container_width=True,key="customs")
    if st.button("Guardar trámites"): st.session_state.aduanas=e.copy(); st.success("Guardado.")
    c=st.session_state.aduanas.copy()
    c["arancel estimado"]=pd.to_numeric(c["valor CIF"],errors="coerce")*pd.to_numeric(c["arancel %"],errors="coerce")/100
    c["cumplimiento"]=np.where(c.documentación.astype(str).str.lower()=="completo","Cumple","Revisar")
    x,y,z=st.columns(3); x.metric("Trámites",len(c)); y.metric("Cumplen",int((c.cumplimiento=="Cumple").sum()))
    z.metric("Arancel estimado",f"${c['arancel estimado'].sum():,.0f}")
    st.dataframe(c,use_container_width=True)
    st.plotly_chart(px.bar(c,x="#trámite",y="arancel estimado",color="cumplimiento",
                           title="Arancel estimado"),use_container_width=True)
    for _,r in c.iterrows():
        (st.success if r.cumplimiento=="Cumple" else st.warning)(f"{r['#trámite']}: {r.cumplimiento}.")

st.divider()
st.caption("PoC académico. Para producción: BD persistente, autenticación, GPS/mapas, datos históricos y validación normativa.")
