// Copyright 2026 Northern.tech AS
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

#ifndef __HOST_ALLOC_H__
#define __HOST_ALLOC_H__

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/*
 * Allocation functions backed by the host (native_sim runner) C library.
 *
 * By default Mender allocates from a Zephyr heap, which is a static array that
 * AddressSanitizer knows nothing about. Routing Mender's allocations to the
 * host malloc() lets ASAN detect heap overflows, use-after-free and leaks in
 * mender-mcu.
 */
void *host_alloc_malloc(size_t size);
void *host_alloc_realloc(void *ptr, size_t size);
void  host_alloc_free(void *ptr);

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* __HOST_ALLOC_H__ */
