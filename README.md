[![pipeline status](https://gitlab.com/b1g_J/tandon.singles/badges/master/pipeline.svg)](https://gitlab.com/b1g_J/tandon.singles/commits/master)

# tandon.singles

A proud [flasq](https://gitlab.com/b1g_J/flasq) app.

### ORM

This project didn't seem particularly interesting, so I implemented my own custom ORM to make it more Spicy. 
It features dynamic model creation, with on the fly relationship detection and resolution. 
It uses an SQL query generator engine that I also implemented for this project.

To use the ORM, all you need to do is query a table like so:
```python
from web.orm import Query

# new_photo will be a dynamically generated model object
new_photo = Query('Photo').new(photoOwner='admin')

# make changes to your object, then update it like this
new_photo.filePath = '/route/to/file'
new_photo.update()

# admin will be a dynamically generated model object
admin = Query('Person').find(username='admin').first()

# The model will automatically detect that you are 
# trying to accessing a relationship, and fetch all 
# Photo objects that are associated with admin as a 
# python list.
admins_photos = admin.photos
```

### Sql Engine

The query engine is quite simple and easy to use.

```python
from web.orm import Sql

# admin will be a dynamically generated model object
admin = Sql.SELECTFROM('Person').WHERE(username='admin').first()

# new_user will be a dynamically generated model object
new_user = Sql.INSERT(username='new_user').INTO('Person').do()

# to get the raw sql being generated for a query
raw_sql, args = Sql.SELECTFROM('Photo').JOIN('Person').WHERE(username='admin').gen()

```

# Maintainer
- big_J
