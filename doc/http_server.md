# HTTP Server Tasarımı

## Issue Credential Endpointleri

### GET /credoffer
returns `cred_offer_json`

Hangi tip cred'in verilebileceğini döndürür. State'e gerek yok. Verebilecegi tum credentialleri JSON array seklinde döndürür.

Prover `cred_offer_json` u aldıktan sonra `cred_req_json` u oluşturur.

### POST /credrequest
body'de `cred_req_json` bulunur. 

#### issue cred (olumlu)
returns `201`
headers `Location`

Server credential'i oluşturur ve location `Location`
headeri ile Client'a (Prover) credential'in serverde hangi URL'de (`/cred/<UUID>`) olduğunu döner. Bu URL tahmin edilemez olmalıdır ve kullanıcı buraya eriştikten sonra bir daha kullanılmamalıdır. 

That the creation happened (the )
Where to find the new thing (the Location header)

#### hata
returns `409`

Server (Issuer) credential oluşturmak istemezse `409` döner.

### GET /cred/<UUID>

Client (Prover) oluşturulan credential'i JSON şeklinde alır ve cüzdanına kaydeder. Server 

## Problemler

- Servis keşfi
    - HTTP endpointler nasıl keşfedilecek ? 
- Indy ile ilgili server threadleri nasıl yönetilmeli.