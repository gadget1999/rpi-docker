#!/bin/bash

function check_env() {
 local VARS=$1
 for VAR in ${VARS[*]}; do
  if [[ ${!VAR} == "" ]]; then
   echo "Invalid ENV variables found: $VAR"
   exit 1
  fi
 done
}

check_env "USER SHARE"

CONFIG_FILE="/etc/samba/smb.conf"

initialized=`getent passwd |grep -c '^smbuser:'`

hostname=`hostname`
set -e
if [ $initialized = "0" ]; then
  adduser smbuser -SHD

  cat >"$CONFIG_FILE" <<EOT
[global]
workgroup = WORKGROUP
netbios name = $hostname
server string = $hostname
server min protocol = SMB2_10
security = user
create mask = 0777
directory mask = 0777
force create mode = 0777
force directory mode = 0777
#force user = smbuser
#force group = smbuser
load printers = no
printing = bsd
printcap name = /dev/null
disable spoolss = yes
guest account = nobody
max log size = 50
map to guest = bad user
#socket options = TCP_NODELAY SO_RCVBUF=8192 SO_SNDBUF=8192
local master = no
dns proxy = no
EOT
    
  IFS=: read username password <<<"$USER"
  echo -n "'$username' "
  adduser "$username" -u 1001 -SHD
  echo -n "with password '$password' "
  echo "$password" |tee - |smbpasswd -s -a "$username"
  echo "DONE"

  IFS=: read sharename sharepath readwrite users <<<"$SHARE"
  echo -n "'$sharename' "
  echo "[$sharename]" >>"$CONFIG_FILE"
  echo -n "path '$sharepath' "
  echo "path = \"$sharepath\"" >>"$CONFIG_FILE"
  echo -n "read"
  if [[ "rw" = "$readwrite" ]] ; then
    echo -n "+write "
    echo "read only = no" >>"$CONFIG_FILE"
    echo "writable = yes" >>"$CONFIG_FILE"
  else
    echo -n "-only "
    echo "read only = yes" >>"$CONFIG_FILE"
    echo "writable = no" >>"$CONFIG_FILE"
  fi
  if [[ -z "$users" ]] ; then
    echo -n "for guests: "
    echo "browseable = yes" >>"$CONFIG_FILE"
    echo "guest ok = yes" >>"$CONFIG_FILE"
    echo "public = yes" >>"$CONFIG_FILE"
  else
    echo -n "for users: "
    users=$(echo "$users" |tr "," " ")
    echo -n "$users "
    echo "valid users = $users" >>"$CONFIG_FILE"
    echo "write list = $users" >>"$CONFIG_FILE"
    echo "admin users = $users" >>"$CONFIG_FILE"
  fi
  echo "DONE"
fi

nmbd -D
smbd -FS --configfile="$CONFIG_FILE" < /dev/null