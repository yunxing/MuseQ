def proxy_mangle_request(req):
    req.setHeader("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.172 Safari/537.22" "http://f1.xiami.net/23375/14916/03_1771160554_3733540.mp3")
    return req

# def proxy_mangle_response(res):
#     v = res.getHeader("Content-Type")
#     if len(v) > 0 and "text/html" in v[0]:
#         res.body = res.body.replace("Google", "elgooG")
#     return res
