#!/usr/bin/env python3
"""Apply minimal, auditable storefront fallback to ipatool 2.8.1.
Legacy storefront IDs are copied from ipatool v2.8.0, not hard-coded to VN/US.
No Apple credentials are logged, transmitted, or persisted by this patch.
"""
from pathlib import Path
import re
import sys

root=Path(sys.argv[1])
legacy=Path(sys.argv[2]) / "pkg/appstore/storefront.go"
source=legacy.read_text(encoding="utf-8")
match=re.search(r'var storeFronts = map\[string\]string\{.*?\n\}',source,re.S)
assert match,"Original v2.8.0 storefront mapping missing"
mapping=match.group().replace("var storeFronts =", "var fallbackStoreFronts =",1)
assert '"VN": "143471"' in mapping and '"US": "143441"' in mapping
out=root/"pkg/appstore/storefront_fallback_vn.go"
out.write_text("""package appstore

import "strings"

// Proven known storefront country IDs from official ipatool v2.8.0.
// Used ONLY when Apple dynamically discovering storefronts fails.
"""+mapping+"""

func fallbackCountryCode(storeFront string) string {
    identifier := storefrontIdentifier(storeFront)
    for country, id := range fallbackStoreFronts {
        if id == identifier {
            return country
        }
    }
    return ""
}

func LegacyCountryForStoreFront(storeFront string) string {
    return strings.ToUpper(fallbackCountryCode(storeFront))
}

func (t *appstore) restoreFallbackStorefronts() {
    codes := make(map[string]string, len(fallbackStoreFronts))
    for country, id := range fallbackStoreFronts {
        codes[id] = country
    }
    t.storefrontCountryCodes = codes
}
""",encoding="utf-8")

p=root/"pkg/appstore/storefront.go"
c=p.read_text(encoding="utf-8")
a='''if err != nil {
        return fmt.Errorf("available storefronts request failed: %w", err)
    }'''
b='''if res.StatusCode != gohttp.StatusOK {
        return NewErrorWithMetadata(errors.New("available storefronts request failed"), res)
    }'''
# Go upstream uses tabs, match with regexp and leave *other functions* untouched.
regex1=r'(res, err := t\.storefrontClient\.Send\(http\.Request\{\s*URL:\s*availableStorefrontsURL,.*?\}\)\s*)if err != nil \{\s*return fmt\.Errorf\("available storefronts request failed: %w", err\)\s*\}'
m=re.search(regex1,c,re.S)
assert m and len(m.group())<900,"Unexpected storefront fetch structure"
sub=m.group(1)+'''if err != nil {
        t.restoreFallbackStorefronts()
        return nil
    }'''
c=c[:m.start()]+sub+c[m.end():]
regex2=r'if res\.StatusCode != gohttp\.StatusOK \{\s*return NewErrorWithMetadata\(errors\.New\("available storefronts request failed"\), res\)\s*\}'
c,n=re.subn(regex2,'''if res.StatusCode != gohttp.StatusOK {
        t.restoreFallbackStorefronts()
        return nil
    }''',c,count=1)
assert n==1,"No storefront response error branch"
p.write_text(c,encoding="utf-8")

auth=root/"cmd/auth.go"
c=auth.read_text(encoding="utf-8")
anchor='''Str("email", output.Account.Email).
\t\t\t\tBool("success", true).'''
# Two occurrences (login, info); replace only occurrence after 'func infoCmd'.
start=c.index('func infoCmd()')
s=c[start:]
assert s.count(anchor)==1, "auth info logging shape changed"
s=s.replace(anchor,'''Str("email", output.Account.Email).
                Str("storeFront", output.Account.StoreFront).
\t\t\t\tStr("country", appstore.LegacyCountryForStoreFront(output.Account.StoreFront)).
\t\t\t\tBool("success", true).''')
c=c[:start]+s
auth.write_text(c,encoding="utf-8")
print("ipatool 2.8.1 patched: dynamic storefront fallback + country-only auth info")
