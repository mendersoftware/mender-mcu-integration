// Copyright 2025 Northern.tech AS
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

/* Zephyr's config-tls-generic.h defines this macro to the value of
   CONFIG_MBEDTLS_SSL_MAX_CONTENT_LEN. However, that config value is used for
   both input and output content and we can only use smaller output content
   length because how much data is sent to us is not under our control (the
   max_fragment_len TLS 1.2 extension seems to be ignored by the webservers we
   communicate with). Prevent redefinition warnings by undefining the macro
   first. */
#ifdef MBEDTLS_SSL_OUT_CONTENT_LEN
#undef MBEDTLS_SSL_OUT_CONTENT_LEN
#endif
#define MBEDTLS_SSL_OUT_CONTENT_LEN 4096
