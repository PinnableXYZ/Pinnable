Test iweb.eth resolving:

```
curl "https://dns.eth.limo/dns-query?name=design.iweb.eth&type=TXT"
```

Output:

```
{"Status":"0","TC":false,"Question":[{"name":"design.iweb.eth","type":16}],"Answer":[{"name":"design.iweb.eth","data":"dnslink=/ipfs/bafybeihtoajol6nbf3kvimfuspkopq643aatgvjmdugkgfpzbm25qoys3y","type":16,"ttl":300}]}
```
