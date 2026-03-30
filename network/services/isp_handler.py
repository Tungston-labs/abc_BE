from services.stampede import fetch_stampede_data


def fetch_isp_data(mapping):
    isp_name = mapping.isp.name.lower()

    if isp_name == "stampede":
        return fetch_stampede_data(mapping)

    # future ISPs
    # elif isp_name == "railwire":
    #     return fetch_railwire_data(mapping)

    else:
        raise Exception("Unsupported ISP")