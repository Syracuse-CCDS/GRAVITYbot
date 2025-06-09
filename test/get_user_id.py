import panoptes_client

user = next(panoptes_client.User.where(login="GRAVITYbot"))
print(user.id)
