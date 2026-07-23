from network.services.stampede import fetch_stampede_data
from network.services.extranet import fetch_extranet_data


def fetch_isp_data(mapping):
    isp_name = mapping.isp.name.strip().lower()

    print(f"📡 Provider : {mapping.isp.name}")
    print(f"👤 Partner  : {mapping.partner_name}")

    if isp_name == "stampede":
        print("➡ Calling Stampede API")
        return fetch_stampede_data(mapping)

    elif isp_name in ["xtra net", "extranet"]:
        print("➡ Calling XTRA NET API")
        return fetch_extranet_data(mapping)

    raise Exception(f"Unsupported ISP: {isp_name}")