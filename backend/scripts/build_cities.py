"""Regenerate ``backend/data/cities.json`` from its authoritative sources.

The bundled snapshot backs ``/meta/cities`` (PRD 7.3: 中国地级市 + 全球主要城市,
GeoNames / 地图 API 离线快照). It ships as static data so the API stays offline-capable
and deterministic; run this script to refresh it.

    cd backend && python scripts/build_cities.py

Sources
-------
* DataV.GeoAtlas — PRC administrative divisions to 地级 level with each seat's
  coordinates. Used for China because it carries simplified-Chinese names and the
  official 行政区划 codes.
* GeoNames ``cities1000`` — world city coordinates (CC-BY 4.0, geonames.org). The
  Chinese labels for non-PRC cities are curated below rather than scraped, because
  GeoNames' untagged alternate-name list mixes Japanese and historical renderings.
"""

from __future__ import annotations

import io
import json
import tempfile
import urllib.request
import zipfile
from pathlib import Path

DATAV = "https://geo.datav.aliyun.com/areas_v3/bound/{adcode}_full.json"
GEONAMES_DUMP = "http://download.geonames.org/export/dump/cities1000.zip"
GEONAMES_CACHE = Path(tempfile.gettempdir()) / "geonames-cities1000.txt"
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "cities.json"

# Municipalities and SARs have no 地级 children in DataV — their children are 区 —
# so the province-level record is itself the city.
PROVINCE_LEVEL_CITIES = {"110000", "120000", "310000", "500000", "810000", "820000"}

# Provinces DataV publishes without a subdivision file; TAIWAN_CITIES below covers 台湾.
GEONAMES_ONLY_PROVINCES = {"710000"}

# Official division suffixes that are noise in a search label.
CITY_NAME_SUFFIXES = ("市", "特别行政区")

# 地级 divisions named after the prefecture rather than a city, so users search for
# the 县级市 beneath them (延边 → 延吉). Those are pulled in as extra entries.
PREFECTURE_NAME_SUFFIXES = ("自治州", "盟", "地区")

# DataV's official provincial names reduced to the label shown beside a city.
PROVINCE_SHORT_NAMES = {
    "内蒙古自治区": "内蒙古",
    "广西壮族自治区": "广西",
    "西藏自治区": "西藏",
    "宁夏回族自治区": "宁夏",
    "新疆维吾尔自治区": "新疆",
    "香港特别行政区": "香港",
    "澳门特别行政区": "澳门",
}

# 台湾's subdivisions are absent from DataV, so its cities come from GeoNames.
TAIWAN_CITIES = [
    ("台北", "台湾", "Taipei"),
    ("新北", "台湾", "New Taipei City"),
    ("桃园", "台湾", "Taoyuan"),
    ("高雄", "台湾", "Kaohsiung"),
    ("台中", "台湾", "Taichung"),
    ("台南", "台湾", "Tainan"),
    ("新竹", "台湾", "Hsinchu"),
    ("基隆", "台湾", "Keelung"),
    ("嘉义", "台湾", "Chiayi City"),
    ("屏东", "台湾", "Pingtung"),
    ("花莲", "台湾", "Hualien City"),
]

# (Chinese city, Chinese country, GeoNames name) for the 全球主要城市 tier.
WORLD_CITIES = [
    ("东京", "日本", "Tokyo"),
    ("大阪", "日本", "Osaka"),
    ("京都", "日本", "Kyoto"),
    ("横滨", "日本", "Yokohama"),
    ("札幌", "日本", "Sapporo"),
    ("首尔", "韩国", "Seoul"),
    ("釜山", "韩国", "Busan"),
    ("仁川", "韩国", "Incheon"),
    ("平壤", "朝鲜", "Pyongyang"),
    ("新加坡", "新加坡", "Singapore"),
    ("吉隆坡", "马来西亚", "Kuala Lumpur"),
    ("雅加达", "印度尼西亚", "Jakarta"),
    ("曼谷", "泰国", "Bangkok"),
    ("芭提雅", "泰国", "Pattaya"),
    ("清迈", "泰国", "Chiang Mai"),
    ("胡志明市", "越南", "Ho Chi Minh City"),
    ("河内", "越南", "Hanoi"),
    ("金边", "柬埔寨", "Phnom Penh"),
    ("万象", "老挝", "Vientiane"),
    ("仰光", "缅甸", "Yangon"),
    ("马尼拉", "菲律宾", "Manila"),
    ("宿务", "菲律宾", "Cebu City"),
    ("加德满都", "尼泊尔", "Kathmandu"),
    ("新德里", "印度", "New Delhi"),
    ("孟买", "印度", "Mumbai"),
    ("加尔各答", "印度", "Kolkata"),
    ("班加罗尔", "印度", "Bengaluru"),
    ("卡拉奇", "巴基斯坦", "Karachi"),
    ("科伦坡", "斯里兰卡", "Colombo"),
    ("迪拜", "阿联酋", "Dubai"),
    ("阿布扎比", "阿联酋", "Abu Dhabi"),
    ("多哈", "卡塔尔", "Doha"),
    ("利雅得", "沙特阿拉伯", "Riyadh"),
    ("麦加", "沙特阿拉伯", "Mecca"),
    ("耶路撒冷", "巴勒斯坦", "Jerusalem"),
    ("巴格达", "伊拉克", "Baghdad"),
    ("德黑兰", "伊朗", "Tehran"),
    ("伊斯坦布尔", "土耳其", "Istanbul"),
    ("安卡拉", "土耳其", "Ankara"),
    ("莫斯科", "俄罗斯", "Moscow"),
    ("圣彼得堡", "俄罗斯", "Saint Petersburg"),
    ("华沙", "波兰", "Warsaw"),
    ("布拉格", "捷克", "Prague"),
    ("布达佩斯", "匈牙利", "Budapest"),
    ("维也纳", "奥地利", "Vienna"),
    ("伯尔尼", "瑞士", "Berne"),
    ("阿姆斯特丹", "荷兰", "Amsterdam"),
    ("布鲁塞尔", "比利时", "Brussels"),
    ("柏林", "德国", "Berlin"),
    ("慕尼黑", "德国", "Munich"),
    ("巴黎", "法国", "Paris"),
    ("马赛", "法国", "Marseille"),
    ("伦敦", "英国", "London"),
    ("曼彻斯特", "英国", "Manchester"),
    ("都柏林", "爱尔兰", "Dublin"),
    ("里斯本", "葡萄牙", "Lisbon"),
    ("马德里", "西班牙", "Madrid"),
    ("巴塞罗那", "西班牙", "Barcelona"),
    ("罗马", "意大利", "Rome"),
    ("米兰", "意大利", "Milan"),
    ("雅典", "希腊", "Athens"),
    ("斯德哥尔摩", "瑞典", "Stockholm"),
    ("奥斯陆", "挪威", "Oslo"),
    ("赫尔辛基", "芬兰", "Helsinki"),
    ("哥本哈根", "丹麦", "Copenhagen"),
    ("基辅", "乌克兰", "Kyiv"),
    ("明斯克", "白俄罗斯", "Minsk"),
    ("塔什干", "乌兹别克斯坦", "Tashkent"),
    ("阿拉木图", "哈萨克斯坦", "Almaty"),
    ("乌兰巴托", "蒙古", "Ulan Bator"),
    ("华盛顿", "美国", "Washington"),
    ("纽约", "美国", "New York City"),
    ("洛杉矶", "美国", "Los Angeles"),
    ("旧金山", "美国", "San Francisco"),
    ("芝加哥", "美国", "Chicago"),
    ("波士顿", "美国", "Boston"),
    ("休斯敦", "美国", "Houston"),
    ("迈阿密", "美国", "Miami"),
    ("西雅图", "美国", "Seattle"),
    ("亚特兰大", "美国", "Atlanta"),
    ("檀香山", "美国", "Honolulu"),
    ("渥太华", "加拿大", "Ottawa"),
    ("多伦多", "加拿大", "Toronto"),
    ("蒙特利尔", "加拿大", "Montreal"),
    ("温哥华", "加拿大", "Vancouver"),
    ("卡尔加里", "加拿大", "Calgary"),
    ("墨西哥城", "墨西哥", "Mexico City"),
    ("哈瓦那", "古巴", "Havana"),
    ("利马", "秘鲁", "Lima"),
    ("波哥大", "哥伦比亚", "Bogota"),
    ("圣地亚哥", "智利", "Santiago"),
    ("布宜诺斯艾利斯", "阿根廷", "Buenos Aires"),
    ("圣保罗", "巴西", "Sao Paulo"),
    ("里约热内卢", "巴西", "Rio de Janeiro"),
    ("悉尼", "澳大利亚", "Sydney"),
    ("墨尔本", "澳大利亚", "Melbourne"),
    ("珀斯", "澳大利亚", "Perth"),
    ("布里斯班", "澳大利亚", "Brisbane"),
    ("奥克兰", "新西兰", "Auckland"),
    ("惠灵顿", "新西兰", "Wellington"),
    ("开罗", "埃及", "Cairo"),
    ("亚历山大", "埃及", "Alexandria"),
    ("开普敦", "南非", "Cape Town"),
    ("约翰内斯堡", "南非", "Johannesburg"),
    ("内罗毕", "肯尼亚", "Nairobi"),
    ("拉各斯", "尼日利亚", "Lagos"),
    ("卡萨布兰卡", "摩洛哥", "Casablanca"),
]


def fetch_json(url: str) -> dict:
    """Download and decode a JSON document."""
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def short_city_name(name: str) -> str:
    """Reduce an official division name to the label a user searches for.

    Only the China tier passes through here, so stripping 市 is safe — the one
    curated label that keeps it (胡志明市) comes from ``WORLD_CITIES`` verbatim.
    """
    for suffix in CITY_NAME_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix) + 1:
            return name[: -len(suffix)]
    return name


def short_province_name(name: str) -> str:
    """Reduce a full provincial name to the label shown beside a city."""
    if name in PROVINCE_SHORT_NAMES:
        return PROVINCE_SHORT_NAMES[name]
    for suffix in ("省", "市"):
        if name.endswith(suffix) and len(name) > 2:
            return name[: -len(suffix)]
    return name


def load_geonames() -> dict[str, list[str]]:
    """Map GeoNames city names to their largest matching record (a name can repeat).

    The dump is cached under the system temp directory because curated names are
    corrected against it, which means re-running the script a few times per refresh.
    """
    if GEONAMES_CACHE.exists():
        text = GEONAMES_CACHE.read_text(encoding="utf-8")
    else:
        dump = io.BytesIO(urllib.request.urlopen(GEONAMES_DUMP, timeout=180).read())
        with zipfile.ZipFile(dump) as archive:
            text = archive.read("cities1000.txt").decode("utf-8")
        GEONAMES_CACHE.write_text(text, encoding="utf-8")

    best: dict[str, list[str]] = {}
    for line in text.splitlines():
        row = line.split("\t")
        population = int(row[14]) if row[14] else 0
        for key in {row[1], row[2]}:
            if key and (key not in best or population > int(best[key][14] or 0)):
                best[key] = row
    return best


def lookup(geonames: dict[str, list[str]], label: str, region: str, english: str) -> dict:
    """Build one snapshot entry from a GeoNames record."""
    row = geonames[english]
    return {"name": label, "province": region, "lat": round(float(row[4]), 4), "lon": round(float(row[5]), 4)}


def resolve_geonames(geonames: dict[str, list[str]], wanted: list[tuple[str, str, str]]) -> list[dict]:
    """Resolve every curated entry, reporting all wrong GeoNames spellings in one go."""
    missing = [f"{english} ({label})" for label, region, english in wanted if english not in geonames]
    if missing:
        raise SystemExit("GeoNames has no record named: " + ", ".join(missing))
    return [lookup(geonames, label, region, english) for label, region, english in wanted]



def entry(name: str, province_name: str, center: list) -> dict:
    """One snapshot record from a division name and its ``[lon, lat]`` center."""
    return {
        "name": short_city_name(name),
        "province": province_name,
        "lat": round(float(center[1]), 4),
        "lon": round(float(center[0]), 4),
    }


def county_cities(prefecture: dict, province_name: str) -> list[dict]:
    """The 县级市 inside a 自治州/盟/地区, which are the names people search for.

    DataV labels such a division after the prefecture (延边朝鲜族自治州) while users know
    its towns (延吉, 珲春). The 州 itself stays in the snapshot as well, so both work.
    """
    adcode = str(prefecture["properties"]["adcode"])
    children = fetch_json(DATAV.format(adcode=adcode)).get("features", [])
    return [
        entry(c["properties"]["name"], province_name, c["properties"]["center"])
        for c in children
        if c["properties"]["name"].endswith("市") and c["properties"].get("center")
    ]


def build_china() -> list[dict]:
    """Every PRC 地级 administrative seat, plus the province-level municipalities."""
    provinces = fetch_json(DATAV.format(adcode="100000"))["features"]
    cities: list[dict] = []

    for province in provinces:
        props = province["properties"]
        adcode = str(props["adcode"])
        if not adcode.isdigit() or adcode in GEONAMES_ONLY_PROVINCES:
            continue
        province_name = short_province_name(props["name"])
        children = (
            [province]
            if adcode in PROVINCE_LEVEL_CITIES
            else fetch_json(DATAV.format(adcode=adcode))["features"]
        )
        for child in children:
            center = child["properties"].get("center")
            if not center:
                continue
            name = child["properties"]["name"]
            cities.append(entry(name, province_name, center))
            if name.endswith(PREFECTURE_NAME_SUFFIXES):
                cities += county_cities(child, province_name)
    return cities


def main() -> None:
    """Fetch both sources, merge them and rewrite the bundled snapshot."""
    geonames = load_geonames()
    cities = build_china()
    cities += resolve_geonames(geonames, TAIWAN_CITIES + WORLD_CITIES)

    OUTPUT.write_text(json.dumps(cities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(cities)} cities to {OUTPUT}")


if __name__ == "__main__":
    main()
