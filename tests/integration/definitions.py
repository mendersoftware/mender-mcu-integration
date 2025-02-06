# Copyright 2024 Northern.tech AS
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

################
# Callbacks
################

# Callbacks defined in the update module
UM_DOWNLOAD_CALLBACK = "UM_DOWNLOAD_CALLBACK"
UM_INSTALL_CALLBACK = "UM_INSTALL_CALLBACK"
UM_REBOOT_CALLBACK = "UM_REBOOT_CALLBACK"
UM_VERIFY_REBOOT_CALLBACK = "UM_VERIFY_REBOOT_CALLBACK"
UM_COMMIT_CALLBACK = "UM_COMMIT_CALLBACK"
UM_ROLLBACK_CALLBACK = "UM_ROLLBACK_CALLBACK"
UM_ROLLBACK_REBOOT_CALLBACK = "UM_ROLLBACK_REBOOT_CALLBACK"
UM_FAILURE_CALLBACK = "UM_FAILURE_CALLBACK"


# Callback defined in callbacks.h and used in main
NETWORK_CONNECT_CALLBACK = "NETWORK_CONNECT_CALLBACK"
NETWORK_RELEASE_CALLBACK = "NETWORK_RELEASE_CALLBACK"
DEPLOYMENT_STATUS_CALLBACK = "DEPLOYMENT_STATUS_CALLBACK"
RESTART_CALLBACK = "RESTART_CALLBACK"
GET_IDENTITY_CALLBACK = "GET_IDENTITY_CALLBACK"


################
# Variables
################

# Update module requires reboot
UM_REQUIRES_REBOOT = "UM_REQUIRES_REBOOT"
# Update module supports rollback
UM_SUPPORTS_ROLLBACK = "UM_SUPPORTS_ROLLBACK"

# Mac address used in identity (used in src/callback.c)
MAC_ADDRESS = "MAC_ADDRESS"
