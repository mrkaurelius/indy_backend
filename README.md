# indy-backend

Credential issue etme ve Authn endpointleri. 

## issue credentail

ornekti uygulamanin HTTP mesajlari ile yapilmasi lazim.

After Trust Anchor has successfully created and stored a Cred Definition using Anonymous Credentials,
Prover's wallet is created and opened, and used to generate Prover's Master Secret.
After that, Trust Anchor generates Credential Offer for given Cred Definition, using Prover's DID
Prover uses Credential Offer to create Credential Request
Trust Anchor then uses Prover's Credential Request to issue a Credential.
Finally, Prover stores Credential in its wallet.

1. credential offer

```python
print_log('\n14. Issuer (Trust Anchor) is creating a Credential Offer for Prover\n')
cred_offer_json = await anoncreds.issuer_create_credential_offer(issuer_wallet_handle,
                                                                cred_def_id)
```

2. credential request

```python
print_log('\n15. Prover creates Credential Request for the given credential offer\n')
(cred_req_json, cred_req_metadata_json) = \
    await anoncreds.prover_create_credential_req(prover_wallet_handle,
                                                    prover_did,
                                                    cred_offer_json,
                                                    cred_def_json,
                                                    prover_link_secret_name)
```

Burada kaldim