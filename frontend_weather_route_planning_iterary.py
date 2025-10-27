import math
import json
from datetime import date, datetime
from typing import List, Dict, Tuple, Optional

import requests
import pandas as pd
import streamlit as st
import pydeck as pdk


# 
st.set_page_config(page_title="PTA — Weather & Routing", '''page_icon="🌦️"''', layout="wide")

# 侧边栏改后端地址，默认指向本机Flask
if "API_BASE" not in st.session_state:
    st.session_state.API_BASE = "http://127.0.0.1:5000"



def ping_backend(api_base: str) -> Tuple[bool, str]:
    """
    看后端在不在线。
    """
    try:
        resp = requests.get(f"{api_base}/api/ping", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            msg = data.get("message", "pong")
            return True, f"Ping OK: {msg}"
        return False, f"Ping failed: HTTP {resp.status_code}"
    except Exception as e:
        return False, f"Ping failed: {e}"

def call_weather_alerts(api_base: str, city: str, d: date) -> Dict:
    """
    尝试调用后端的天气提醒接口（你可以把它对到 agent 的 KnowledgeBase / external weather）。
    推荐 GET /api/weather_alerts?city=xxx&date=yyyy-mm-dd
    返回结构（建议）：
    {
      "success": true,
      "city": "Sydney",
      "date": "2025-10-24",
      "weather": {"summary":"Showers", "temp_c":18, "wind_kph":22},
      "alerts": [
        {"type":"Heavy Rain", "severity":"high", "start":"09:00", "end":"14:00", "advice":"Bring raincoat"}
      ]
    }
    """
    try:
        r = requests.get(
            f"{api_base}/api/weather_alerts",
            params={"city": city, "date": d.isoformat()},
            timeout=10
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    # 假数据”
    return {
        "success": True,
        "city": city,
        "date": d.isoformat(),
        "weather": {"summary": "Showers likely", "temp_c": 18, "wind_kph": 20},
        "alerts": [
            {"type": "Heavy Rain", "severity": "high", "start": "09:00", "end": "13:00",
             "advice": "带雨具、备替代室内行程"}
        ]
    }

def haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """两点直线球面距离，单位 km。只是为了给纯文字步骤一个“像样”的里程数。"""
    lat1, lon1 = a
    lat2, lon2 = b
    R = 6371.0
    p = math.pi / 180.0
    dlat = (lat2 - lat1) * p
    dlon = (lon2 - lon1) * p
    x = (math.sin(dlat/2)**2
         + math.cos(lat1*p)*math.cos(lat2*p)*math.sin(dlon/2)**2)
    return 2 * R * math.asin(min(1, math.sqrt(x)))

def decode_polyline(encoded: str) -> List[Tuple[float, float]]:
    """
    可选：如果后端返回 Google encoded polyline，这里解成点串画线。
    不想引依赖，就贴一个小解码器（够用就行）。
    """
    points, index, lat, lon = [], 0, 0, 0
    while index < len(encoded):
        shift, result = 0, 0
        while True:
            b = ord(encoded[index]) - 63; index += 1
            result |= (b & 0x1f) << shift; shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat
        shift, result = 0, 0
        while True:
            b = ord(encoded[index]) - 63; index += 1
            result |= (b & 0x1f) << shift; shift += 5
            if b < 0x20:
                break
        dlon = ~(result >> 1) if (result & 1) else (result >> 1)
        lon += dlon
        points.append((lat / 1e5, lon / 1e5))
    return points

def known_place(name: str) -> Optional[Tuple[float, float]]:
    """
    简易“伪地理库”：如果用户输入了若干关键地标名，就给出坐标（够验证就行）。
    你也可以换成真正的 /api/geocode。
    """
    key = name.strip().lower()
    table = {
        "sydney opera house": (-33.8567844, 151.2152967),
        "circular quay station": (-33.861, 151.2108),
        "town hall": (-33.8732, 151.2065),
        "unsw": (-33.917347, 151.231267),
        "uow": (-34.405, 150.878),
        "usyd": (-33.888, 151.187),
        "darling harbour": (-33.871, 151.200),
    }
    return table.get(key, None)

'''def mock_route(origin: Tuple[float, float], dest: Tuple[float, float]) -> Dict:
    """
    兜底方案：如果后端未就绪，也没有 polyline，那就用 2 点直线插值出一条“像路”的线。
    不是导航，但能证明“地图图层”和“文字步骤”都工作了。
    """
    # 简单插值 20 个点
    lat1, lon1 = origin
    lat2, lon2 = dest
    pts = [(lat1 + (lat2-lat1)*t/19.0, lon1 + (lon2-lon1)*t/19.0) for t in range(20)]
    km = haversine_km(origin, dest)
    steps = [
        {"instruction": f"从起点出发，沿直线前进约 {km:.1f} km（示意）", "distance_km": km, "duration_min": km/4.5*60 if km>0 else 3}
    ]
    return {"success": True, "points": pts, "steps": steps}
'''
def call_route_plan(api_base: str, origin_txt: str, dest_txt: str, mode: str) -> Dict:
    """
    尝试 POST /api/route_plan（推荐请求体）：
    {
      "origin": "Sydney Opera House" 或 {"lat":..., "lon":...},
      "destination": "Town Hall"     或 {"lat":..., "lon":...},
      "mode": "walking|driving|transit"
    }
    期望返回：
    {
      "success": true,
      "steps": [{"instruction":"...", "distance_m":..., "duration_min":...}, ...],
      "polyline": "...."  # 可选，或者直接返回 "points":[{"lat":..,"lon":..}, ...]
    }
    """
    # 接后端
    payload = {"origin": origin_txt, "destination": dest_txt, "mode": mode}
    try:
        r = requests.post(f"{api_base}/api/route_plan", json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass

    '''# 假数据
    o = known_place(origin_txt)
    d = known_place(dest_txt)
    if o and d:
        return mock_route(o, d)

    return {
        "success": True,
        "steps": [
            {"instruction": f"从「{origin_txt}」出发，前往「{dest_txt}」。", "distance_m": None, "duration_min": None},
            {"instruction": f"（后端未返回路线，已用占位步骤；等 /api/route_plan 就绪会自动替换）", "distance_m": None, "duration_min": None},
        ]
    }

def to_points_df(points: List[Tuple[float, float]]) -> pd.DataFrame:
    """把点串变成 DataFrame 给地图用。"""
    return pd.DataFrame([{"lat": lat, "lon": lon} for lat, lon in points])

def draw_route_map(points: List[Tuple[float, float]]):
    """
    用 pydeck 画一条“线路 + 端点”。
    st.map 只能点散点；pydeck 的 LineLayer 更像个正经“路线”。
    """
    if not points:
        st.info("No geometry to draw.")
        return

    df_points = to_points_df(points)
    line_layer = pdk.Layer(
        "LineLayer",
        data=df_points,
        get_source_position=["lon", "lat"],
        get_target_position=["lon", "lat"],
        # 连续点需要一条条 segment，这里偷个懒：让每个点与下一个点连线
        # pydeck 没有“自动链式连线”，我们手动喂 segment 数据（轻量构造）
        # ——简单做法：复制一份错位数据并拼成长表：
    )

    # 构造 LineLayer 需要的 segment 形式
    segs = []
    for i in range(len(points) - 1):
        a = points[i]
        b = points[i + 1]
        segs.append({"lon1": a[1], "lat1": a[0], "lon2": b[1], "lat2": b[0]})
    seg_df = pd.DataFrame(segs)
    line_layer = pdk.Layer(
        "LineLayer",
        data=seg_df,
        get_source_position=["lon1", "lat1"],
        get_target_position=["lon2", "lat2"],
        pickable=False,
        auto_highlight=False,
        width_scale=2,
        get_width=4,
    )

    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=pd.DataFrame([
            {"lon": points[0][1], "lat": points[0][0], "size": 10, "label": "Start"},
            {"lon": points[-1][1], "lat": points[-1][0], "size": 10, "label": "End"},
        ]),
        get_position=["lon", "lat"],
        get_radius="size",
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=sum(p[0] for p in points) / len(points),
        longitude=sum(p[1] for p in points) / len(points),
        zoom=12,
    )

    st.pydeck_chart(pdk.Deck(
        initial_view_state=view_state,
        layers=[line_layer, scatter_layer],
        tooltip={"text": "{label}"}
    ))
'''


# 侧边栏
st.sidebar.header("Settings")
api_base_input = st.sidebar.text_input("API_BASE (Flask backend URL)", value=st.session_state.API_BASE)
if api_base_input != st.session_state.API_BASE:
    st.session_state.API_BASE = api_base_input

colA, colB = st.sidebar.columns(2)
with colA:
    if st.button("Ping Backend"):
        ok, msg = ping_backend(st.session_state.API_BASE)
        st.sidebar.write("✅" if ok else "❌", msg)
with colB:
    st.sidebar.caption("If ping fails, the page will use mock data.")

st.sidebar.markdown("---")
st.sidebar.caption("This page is safe to run without a live backend (mock mode).")


# 页面内容
st.title("PTA — Weather Alerts & Route Planning")

tab1, tab2 = st.tabs(["Weather Alerts", "Route Planner"])

with tab1:
    st.subheader("Weather Alerts")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        city = st.text_input("City", value="Sydney")
    with c2:
        d = st.date_input("Date", value=date.today())
    with c3:
        if st.button("Fetch Alerts", use_container_width=True):
            st.session_state["_weather_click"] = True

    if st.session_state.get("_weather_click"):
        data = call_weather_alerts(st.session_state.API_BASE, city, d)
        if not data.get("success"):
            st.error("Backend returned unsuccessful result. Showing raw payload:")
            st.code(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            w = data.get("weather", {})
            st.write(f"**{data.get('city', city)} · {data.get('date', d.isoformat())}**")
            if w:
                st.info(f"Weather: {w.get('summary','-')} | Temp: {w.get('temp_c','-')}°C | Wind: {w.get('wind_kph','-')} km/h")
            alerts = data.get("alerts", [])
            if alerts:
                for i, a in enumerate(alerts, 1):
                    sev = a.get("severity", "info").lower()
                    text = f"**{a.get('type','Alert')}** · {a.get('start','?')}–{a.get('end','?')} · {a.get('advice','')}"
                    if sev in ("high", "severe"):
                        st.warning(text)
                    elif sev in ("critical", "extreme"):
                        st.error(text)
                    else:
                        st.info(text)
            else:
                st.success("No alerts 🎉")
        st.caption("（提示：如果你们的 Flask 还没有 /api/weather_alerts，这里是用内置假数据做展示。）")

with tab2:
    st.subheader("Route Planner")
    c1, c2, c3 = st.columns([3, 3, 1])
    with c1:
        origin = st.text_input("Origin (name or lat,lon)", value="Circular Quay Station")
    with c2:
        destination = st.text_input("Destination (name or lat,lon)", value="Sydney Opera House")
    with c3:
        mode = st.selectbox("Mode", ["walking", "driving", "transit"], index=0)

    if st.button("Get Route", use_container_width=True):
        res = call_route_plan(st.session_state.API_BASE, origin, destination, mode)
        if not res.get("success"):
            st.error("Backend returned unsuccessful result. Showing raw payload:")
            st.code(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            steps = res.get("steps", [])
            poly = res.get("polyline")
            pts = res.get("points")

            # 文字步骤
            st.markdown("#### Directions")
            if steps:
                for i, s in enumerate(steps, 1):
                    seg = s.get("instruction", "")
                    dist = s.get("distance_m")
                    dur = s.get("duration_min")
                    extra = []
                    if dist is not None:
                        extra.append(f"{dist} m")
                    if dur is not None:
                        extra.append(f"{dur:.0f} min")
                    tail = f"  _({' · '.join(extra)})_" if extra else ""
                    st.markdown(f"{i}. {seg}{tail}")
            else:
                st.info("No step-by-step directions provided.")

            # 地图几何：尽量“有就画、没有就算了”
            geom_points: List[Tuple[float, float]] = []
            if isinstance(pts, list) and pts and isinstance(pts[0], dict) and "lat" in pts[0]:
                geom_points = [(p["lat"], p["lon"]) for p in pts]
            elif isinstance(pts, list) and pts and isinstance(pts[0], (list, tuple)):
                geom_points = [(float(a), float(b)) for a, b in pts]
            elif isinstance(poly, str) and poly:
                try:
                    geom_points = decode_polyline(poly)
                except Exception:
                    pass

            if geom_points:
                st.markdown("#### Map")
                draw_route_map(geom_points)
            else:
                st.caption("（后端没给几何；已用文字步骤展示。等几何返回后会自动出现地图。）")

# 底部提示
st.markdown("---")
st.caption("Tip: Hook /api/weather_alerts & /api/route_plan to your agent. This UI will adapt automatically.")

