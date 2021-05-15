# HTTP Server Tasarımı

## Issue Credential Endpointleri

### GET /availablecreds

returns `cred_defs_json`

Hangi tip cred'in verilebileceğini döndürür. State'e gerek yok. Verebilecegi tum credentiallerin idlerini JSON array seklinde döndürür.

### GET /credoffer/<cred_def_id>
returns `cred_offer_json`

*Burası tam olarak dusundugum gibi degil, verilebilecek credentiallerin ıd lerini ilk adımda yayınlamak daha sonra offeri almak gerek offer sonraki adimlarda lazim stateless degil*

gelen cred_def_id ye gore cred_

Prover `cred_offer_json` u aldıktan sonra `cred_req_json` u oluşturur.

### POST /credrequest
body'de `cred_req_json` bulunur. 

#### issue cred (olumlu)
credential'i olusturur ve post isteginin response'u olarak geri doner.

## Problemler

- Servis keşfi
    - HTTP endpointler nasıl keşfedilecek ? 
- Indy ile ilgili server threadleri nasıl yönetilmeli.