from flask import Flask, render_template, request
from ldap3 import Server, Connection, ALL, Tls
import ssl
import re
from collections import defaultdict

app = Flask(__name__)

# Configuration
LDAP_SERVER = 'ldaps://ldaps-eus2.MYKFT.net'
BIND_DN = 'CN=JSE2367,OU=Contractors,OU=Users,OU=Grocery,DC=MYKFT,DC=NET'
BIND_PW = 'ahZbpfLfn9U!Xn4mgmZ4'
BASE_DN = 'DC=MYKFT,DC=NET'

# Optional TLS config (use CERT_NONE only if you're testing)
tls_config = Tls(validate=ssl.CERT_NONE)

def get_user_groups(conn, user_id):
    conn.search(
        BASE_DN,
        f"(samaccountname={user_id})",
        attributes=["memberOf"]
    )
    if not conn.entries:
        return []

    entry = conn.entries[0]
    return entry.memberOf.values if "memberOf" in entry else []

def extract_cn(dn):
    match = re.search(r"CN=([^,]+)", dn, re.IGNORECASE)
    return match.group(1) if match else dn

def get_group_dn_by_cn(conn, cn_name):
    conn.search(
        BASE_DN,
        f"(cn={cn_name})",
        attributes=["distinguishedName"]
    )
    if not conn.entries:
        return None
    return str(conn.entries[0].entry_dn)

def get_group_members(conn, group_dn):
    conn.search(
        BASE_DN,
        f"(distinguishedName={group_dn})",
        attributes=["member"]
    )
    if not conn.entries:
        return []

    return conn.entries[0].member.values if "member" in conn.entries[0] else []

@app.route("/", methods=["GET", "POST"])
def searchByUser():
    user_id = ""
    if request.method == "POST":
      user_id = request.form.get("user", "")
    groups = []
    servers = []
    group_servers = defaultdict(list)
    error = None
    
    if user_id:
        try:
            server = Server(LDAP_SERVER, use_ssl=True, tls=tls_config, get_info=ALL)
            conn = Connection(server, BIND_DN, BIND_PW, auto_bind=True)

            user_group_dns = get_user_groups(conn, user_id)

            groups = [
                extract_cn(dn)
                for dn in user_group_dns
                if extract_cn(dn).lower().startswith("server")
            ]

            for group_cn in groups:
                if re.match(r"servers_.+_(admins|users)", group_cn, re.IGNORECASE):
                    bthag_cn = re.sub(r'_(admins|users)$', '_bthag', group_cn, flags=re.IGNORECASE)
                    bthag_dn = get_group_dn_by_cn(conn, bthag_cn)
                    if bthag_dn:
                        members = get_group_members(conn, bthag_dn)

                        azure_members = [
                            extract_cn(m) for m in members if "azure servers" in m.lower()
                        ]

                        group_servers[group_cn].extend(azure_members)
                        servers.extend(azure_members)

            group_servers = {group: sorted(servers) for group, servers in sorted(group_servers.items())}

            conn.unbind()
        except Exception as e:
            error = str(e)

    # Remove duplicates from flat server list
    servers = sorted(set(servers))

    # Split servers into multiple groups if necessary
    num_groups = len(group_servers)
    num_servers = len(servers)
    num_columns = 5
    split_servers = [servers[i:i + num_columns] for i in range(0, num_servers, num_columns)]

    return render_template(
        "index.html",
        user=user_id,
        groups=sorted(groups),
        servers=sorted(servers),
        group_servers=group_servers,
        error=error,
        SERVER_GROUP_PREFIX="servers_*_bthag",
        split_servers=split_servers,
        num_groups=num_groups,
        num_columns=num_columns
    )



application = app

if __name__ == "__main__":
    app.run(debug=True)
