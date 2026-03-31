from bit_share.api import API

API.discover_request("605a63e35f8f2daa7baa6f5ef8de501799d462ff8e33ac126455fbe49c34277e")
package = API.request_package("605a63e35f8f2daa7baa6f5ef8de501799d462ff8e33ac126455fbe49c34277e", "172.19.0.2")
print(package.filelist)