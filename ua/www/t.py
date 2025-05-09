import xmlrpc.client


# Replace with your SUSE Manager server URL
suma_url = 'http://eus2psusemgr001.mykft.net/rpc/api'
client = xmlrpc.client.ServerProxy(suma_url)

# Authenticate with SUSE Manager
session_key = client.auth.login('admin', 'Kraft@123#')

# List all available roles
available_roles = client.user.listAllRoles(session_key)

# Print the available roles
print("Available Roles:")
for role in available_roles:
    print(role)

# Logout
client.auth.logout(session_key)

