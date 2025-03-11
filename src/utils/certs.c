// Copyright 2024 Northern.tech AS
//
//    Licensed under the Apache License, Version 2.0 (the "License");
//    you may not use this file except in compliance with the License.
//    You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//    Unless required by applicable law or agreed to in writing, software
//    distributed under the License is distributed on an "AS IS" BASIS,
//    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//    See the License for the specific language governing permissions and
//    limitations under the License.

#include "certs.h"

#include <stddef.h>

#include <zephyr/net/tls_credentials.h>

#if defined(CONFIG_NET_SOCKETS_SOCKOPT_TLS)
static const unsigned char primary_certificate[] = {
#include "PrimaryCertificate.cer.inc"
};
#ifdef CONFIG_MENDER_NET_CA_CERTIFICATE_TAG_SECONDARY_ENABLED
static const unsigned char secondary_certificate[] = {
#include "SecondaryCertificate.cer.inc"
};
#endif
#endif

int
certs_add_credentials(void) {
    int ret = 0;

#if defined(CONFIG_NET_SOCKETS_SOCKOPT_TLS)
    ret = tls_credential_add(CONFIG_MENDER_NET_CA_CERTIFICATE_TAG_PRIMARY, TLS_CREDENTIAL_CA_CERTIFICATE, primary_certificate, sizeof(primary_certificate));
    if (ret != 0) {
        return ret;
    }
#ifdef CONFIG_MENDER_NET_CA_CERTIFICATE_TAG_SECONDARY_ENABLED
    ret = tls_credential_add(
        CONFIG_MENDER_NET_CA_CERTIFICATE_TAG_SECONDARY, TLS_CREDENTIAL_CA_CERTIFICATE, secondary_certificate, sizeof(secondary_certificate));
#endif
#endif

    return ret;
}
