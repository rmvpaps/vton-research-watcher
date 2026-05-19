# Running scraper as ecs task

## created cluster in ecs

Used fargate based cluster since its a weekly once job

## Alembic used instead of manual create all

- first time
`alembic init`

- Make sure to import models into env.py. create revision
`alembic revision --autogenerate -m "create article and relevance tables"`
version files created with schema

- if tables already present before alembic
```
alembic stamp head
alembic revision --autogenerate -m "verify_sync"
```
the new version will contain just pass for upgrade downgrade if schema same. else need to cleanup


- Right after making new model changes
`alembic revision --autogenerate -m "create article changes"`

Migrate the changes to DB structure
`alembic upgrade head`

migration folder need to be inserted into sourcecontrol for the image to have this details

## created container image

Created docker file and push to ecr

```
docker build -t scraper:v0 -f Dockerfile_scraper .
aws login --profile rmvpapz
aws ecr create-repository --repository-name research-watcher --region us-east-1
docker tag scraper:v0 {$ACCOUNT__ID}.dkr.ecr.us-east-1.amazonaws.com/research-watcher
aws ecr get-login-password --region us-east-1 --profile rmvpapz| docker login --username AWS --password-stdin {$ACCOUNT__ID}.dkr.ecr.us-east-1.amazonaws.com/research-watcher
docker push {$ACCOUNT__ID}.dkr.ecr.us-east-1.amazonaws.com/research-watcher
```

## created taskdefintion

Reduced .env added to s3 with sensitive data fields removed
S3 bucket file linked to task definition

sensitive data added to secets manager - rds password and llm api key
retrieved in task definintion to environment

pythonpath added to environment in task definition to handle module not found issues

## Dry run for access and connectivity check

running alembic version
```
aws ecs run-task `
  --cluster research-watcher `
  --task-definition aws-scraper:4 `
  --count 1 `
  --launch-type FARGATE `
  --network-configuration "awsvpcConfiguration={subnets=[subnet-033a18eb12effae82],securityGroups=[sg-0b682055b2c6f6bb9],assignPublicIp=ENABLED}"`
  --overrides "containerOverrides=[{name=scraper-app,command=[uv,run,alembic,current]}]" --profile rmvpapz
```

To know status of a task, use describe task

```  
aws ecs describe-tasks --cluster research-watcher --tasks arn:aws:ecs:us-east-1:{$ACCOUNT__ID}:task/research-watcher/5f5bf46f2820470b97f14ac5fd009748 --profile rmvpapz
```

### initial database creation

Use the same docker image for a one-off ecs task to create custom DB for the project by running setupdb.py. this can be done using containeroverride and new command

```
aws ecs run-task `                                     
   --cluster research-watcher `                                                                               
   --task-definition aws-scraper:4 `
   --count 1 `
   --launch-type FARGATE `
   --network-configuration "awsvpcConfiguration={subnets=[subnet-033a18eb12effae82],securityGroups=[sg-0b682055b2c6f6bb9],assignPublicIp=ENABLED}"`
   --overrides "containerOverrides=[{name=scraper-app,command=[uv,run,setupdb.py]}]" --profile rmvpapz  
```
## Migration

Once DB is created, run alembic migrations. alembic requires syncg pg driver which has different ssl mode parameter passed via env and urlprotocol so replaced in env.py

```
aws ecs run-task `                                     
   --cluster research-watcher `                                                                               
   --task-definition aws-scraper:4 `
   --count 1 `
   --launch-type FARGATE `
   --network-configuration "awsvpcConfiguration={subnets=[subnet-033a18eb12effae82],securityGroups=[sg-0b682055b2c6f6bb9],assignPublicIp=ENABLED}"`
   --overrides "containerOverrides=[{name=scraper-app,command=[uv,run,alembic,upgrade,head],environment=[{name=db_sslstring,value=sslmode}]}]" 

```


## Run the actual scraper task

```
aws ecs run-task `                                     
   --cluster research-watcher `                                                                               
   --task-definition aws-scraper:4 `
   --count 1 `
   --launch-type FARGATE `
   --network-configuration "awsvpcConfiguration={subnets=[subnet-033a18eb12effae82],securityGroups=[sg-0b682055b2c6f6bb9],assignPublicIp=ENABLED}"`
   --profile rmvpapz  

```