# indy-backend

Credential issue etme ve Authn endpointleri. İlk aşamada HTTP mesajlaşma geliştirmeyi kolaylaştırmak amacıyla plaintext olacak. Daha sonra mesajlar Authenticated encryption ile şifrelenecek. Burdaki mesajlaşmalar kullanıcıların değil makinelerin anlayabileceği seviyede daha sonra uygulamalar bu mesajları kullanarak kullanıcılarla etkileşecekler.

## notlar

Kutuphane dokumantasyonunda stewardla trust anchor eklemeye calisiyorlar fakat, eklenen did trusth achor olarak degil endorser olarak ekleniyor. Endorser'a trust anchor demek karmasaya yol acsada yanlis olamasa gerek.  

indy SDK dokumantasyonunda ledgere CRED_DEF konulmamis ama areis demosunda konulmus bunun ne gibi etkileri olur ? cevap anoncred docunda. cred def karsi tarafa herhangi bir sekilde de verilebilir. CRED_DEF Tx ile ledgere de gonderilebilir.
```
Credential definition entity contains private and public parts. Private part will be stored in the wallet. Public part will be returned as json intended to be shared with all anoncreds workflow actors usually by publishing CRED_DEF transaction to Indy distributed ledger.
```