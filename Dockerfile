# Copyright (C) 2023-2024 Cisco Systems, Inc. and/or its affiliates. All rights reserved.
#
# Authors: Dave Zhu (yanbzhu@cisco.com)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of mosquitto nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Use the public clamav docker image for debian
FROM clamav/clamav-debian:1.3

RUN set -eux && \
    apt-get update && \
    apt-get upgrade -y && \
    # Install dependencies and Python 3 + the Python Pip package manager
    apt-get install -y libguestfs-tools libmagic1 python3-pip && \
    rm -rf /var/lib/apt/lists/* && \
    sed \
        -e "s|^\#\(MaxFileSize\) .*|\1 0|" \
        -e "s|^\#\(MaxScanSize\) .*|\1 0|" \
        -e "s|^\#\(MaxScanTime\) .*|\1 3600000|" \
        -e "s|^\#\(MaxFiles\) .*|\1 100000|" \
        -e "s|^\#\(MaxRecursion\) .*|\1 20|" \
        -e "s|^\#\(AlertExceedsMax\) .*|\1 yes|" \
      "/etc/clamav/clamd.conf" > "/etc/clamav/clamd.conf.tmp" && \
    mv "/etc/clamav/clamd.conf.tmp" "/etc/clamav/clamd.conf"

WORKDIR /src
COPY . /src/

# Install the scanner and required Python packages.
# This will also place a script executable in the $PATH.
RUN  pip3 install /src
