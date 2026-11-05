# Intermediate certificates

`list.worldfloraonline.org` serves its leaf certificate without the intermediate, so OpenSSL-based clients cannot build the chain. The pipeline adds the published intermediate below to the default trust store. Verification is never disabled.

| File | Subject | Issuer | Source | SHA-256 |
|---|---|---|---|---|
| `GeoTrustTLSRSACAG1.pem` | GeoTrust TLS RSA CA G1 | DigiCert Global Root G2 | http://cacerts.geotrust.com/GeoTrustTLSRSACAG1.crt (the AIA URL in the WFO certificate) | `C0:6E:30:7F:7C:FC:1D:32:FA:72:A4:C0:33:C8:7B:90:01:9A:F2:16:F0:77:5D:64:97:8A:2E:CA:6C:8A:23:0E` |

Expires 2027-11-02.
