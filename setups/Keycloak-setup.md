# Start Keycloak server
```bash
docker run -d --name keycloak-cloudprompt -p 8080:8080 -e KC_BOOTSTRAP_ADMIN_USERNAME=cloudprompt -e KC_BOOTSTRAP_ADMIN_PASSWORD=cloudprompt quay.io/keycloak/keycloak:26.1.0 start-dev
```

# Create new admin account and set password
![create-admin](images/create-admin.png)

![set-pass](images/set-pass.png)

>Assign admin realm role
![assign-role](images/assign-role.png)

>Delete old user admin user

# Create new realm
![new-realm](images/new-realm.png)

# Create first user in the new realm
![new-user](images/new-user.png)

# Create new client
![new-client](images/new-client.png)
![new-client2](images/new-client2.png)
![new-client3](images/new-client3.png)

# Create client scope
![client-scope](images/client-scope.png)

# Add audience mapper to client scope
![audience-mapper](images/audience-mapper.png)

# Assign client scope to client
![assign-client-scope](images/assign-client-scope.png)