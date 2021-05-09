# indy issue credential flow

credential scheme ve definitionu atlandi.

## Offer Credential içeren akış

### 1. **Prover** is creating Link Secret

```python
link_secret_id = await anoncreds.prover_create_master_secret(prover_wallet_handle,
                                                                prover_link_secret_name)
```

### 2. **Issuer** is creating a Credential Offer for Prover

```py
cred_offer_json = await anoncreds.issuer_create_credential_offer(issuer_wallet_handle,
                                                                        cred_def_id)
```

### 3. **Prover** creates Credential Request for the given credential offer

```py
(cred_req_json, cred_req_metadata_json) = \
            await anoncreds.prover_create_credential_req(prover_wallet_handle,
                                                         prover_did,
                                                         cred_offer_json,
                                                         cred_def_json,
                                                         prover_link_secret_name)
```

### 4. **Issuer** creates Credential for Credential Request

```py
cred_values_json = json.dumps({
            "sex": {"raw": "male", "encoded": "5944657099558967239210949258394887428692050081607692519917050011144233"},
            "name": {"raw": "Alex", "encoded": "1139481716457488690172217916278103335"},
            "height": {"raw": "175", "encoded": "175"},
            "age": {"raw": "28", "encoded": "28"}
        })

(cred_json, _, _) = \
            await anoncreds.issuer_create_credential(issuer_wallet_handle,
                                                     cred_offer_json,
                                                     cred_req_json,
                                                     cred_values_json, None, None)                
```

### 5. **Prover** processes and stores received Credential

```py
await anoncreds.prover_store_credential(prover_wallet_handle, None,
                                                cred_req_metadata_json,
                                                cred_json,
                                                cred_def_json, None)
```