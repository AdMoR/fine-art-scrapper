# databricks-jobs

This is a sample project for Databricks, generated via cookiecutter.
While using this project, you need Python 3.X and `pip`

## Installing project requirements

```bash
 brew cask install java
 brew install spark
```

## Install project package in a developer mode

```bash
pip install -r unit-requirements.txt
pip install -e .
```

## Configure your databricks setup

You need to have your `~/.databrickscfg` file setup to deploy your code
```
echo "[DEFAULT]" >> ~/.databrickscfg
echo "host = https://mtv-data-dev.cloud.databricks.com" >> ~/.databrickscfg
echo "token = *********" >> ~/.databrickscfg
```

## Install dbx

cd tools
pip install dbx-0.7.0-py3-none-any.whl


## Testing

For local unit testing, please use `pytest`:
```
pytest tests/unit
```

Check the code style with 
```
 flake8 ./databricks_jobs --count --select=E9,F63,F7,F82 --show-source --statistics &&
 flake8 ./databricks_jobs --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

Deploy your code 
```
dbx deploy 
dbx launch --job=databricks_jobs-popular_reco_job --trace 
```

## Common errors & fix in local testing
```
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES / for multiprocessing issue
export JAVA_HOME=$(/usr/libexec/java_home -v 1.8) / Use Java 8 for debugging. pyarrow pandas_udf easily compatible with java 8
```

## Deployment on Github actions 

Defined in .github/workflows
On master merge, code is deployed on the production env.

If the yaml file must be modified, one can use `act` : 
```
 act -e /Users/amorvan/Documents/code_dw/databricks_dev_repo/databricks_jobs/.github/workflows/deploy_jobs_on_prod_databricks.yml -s DATABRICKS_HOST=https://mtv-data-dev.cloud.databricks.com -s DATABRICKS_TOKEN=XXXXXXX -s SNOWFLAKE_USER=XXXXXXXX -s SNOWFLAKE_PASSWORD=XXXXXX  -s AWS_ONBOARDING_ACCESS_KEY=XXXXXXX -s AWS_ONBOARDING_SECRET_KEY=XXXXXXX -s AWS_S3_ONBOARDING_OUTPUT_BUCKET=mtv-dev-onboarding -s AWS_S3_PANEL_OUTPUT_BUCKET=mtv-dev-panel --verbose
```


## CICD pipeline settings

Please set the following secrets or environment variables. 
Follow the documentation for [GitHub Actions](https://docs.github.com/en/actions/reference) or for [Azure DevOps Pipelines](https://docs.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops&tabs=yaml%2Cbatch):
- `DATABRICKS_HOST`
- `DATABRICKS_TOKEN`


# Sanity checks on recos 

For bookmarks 

```sql
select TITLE, count(distinct USER_ID) as cnt
from backend.bookmark_recording 
join backend.program
on backend.program.id = backend.bookmark_recording.program_id
where backend.bookmark_recording.RESOLVED_AT > current_date - 14
group by TITLE
order by cnt desc
```

For allo ciné

```sql 
with  free_channel as (
 select CHANNEL_ID, TVBUNDLE_ID, bc.NAME, bc.DISPLAY_NAME 
            from backend.rel_tvbundle_channel
            inner join backend.channel as bc on CHANNEL_ID = bc.ID
            where tvbundle_id in (25, 90, 26)
 )
select AFFINITY, backend.program.TITLE, rating
from backend.program_rating
join backend.broadcast
on backend.program_rating.PROGRAM_ID = backend.broadcast.PROGRAM_ID
join backend.program 
on backend.program.ID = backend.broadcast.PROGRAM_ID
left join external_sources.daily_prog_affinity
on backend.program.ID=external_sources.daily_prog_affinity.program_id
join free_channel
on free_channel.CHANNEL_ID = backend.broadcast.CHANNEL_ID
where REF_PROGRAM_CATEGORY_ID = 1 and PROGRAM_RATING_SERVICES_ID = 2 and PROGRAM_RATING_TYPE_ID = 2
and START_AT >= current_date and START_AT <= current_date + 7
order by rating desc
```

For celeb_points

```sql 
with temp as (
  select PERSON_ID, FIRST_NAME, LAST_NAME, count(*) as cnt 
  from backend.person
  left outer join backend.user_follow_person 
  on PERSON_ID = ID
  where source = 'molotov'
  group by PERSON_ID, FIRST_NAME, LAST_NAME
),
 rel_person_prog as (
    select PROGRAM_ID, PERSON_ID
    from backend.rel_program_person
    UNION (
      select program_id, person_id 
      from backend.rel_episode_person 
      join backend.episode 
      on episode_id = id 
     )
),
pop_score_per_program as (
  select p.PROGRAM_ID, SUM(coalesce(temp.cnt, 0)) as total_celeb_points
    from temp
    join rel_person_prog as p
    on p.PERSON_ID = temp.PERSON_ID
  group by p.PROGRAM_ID
),
 free_channel as (
 select CHANNEL_ID, TVBUNDLE_ID, bc.NAME, bc.DISPLAY_NAME 
            from backend.rel_tvbundle_channel
            inner join backend.channel as bc on CHANNEL_ID = bc.ID
            where tvbundle_id in (25, 90, 26, 31, 60)
 )

select distinct AFFINITY, pop_score_per_program.PROGRAM_ID, bp.TITLE, total_celeb_points
from pop_score_per_program
join backend.program as bp
on ID = pop_score_per_program.PROGRAM_ID
left join external_sources.daily_prog_affinity
on bp.id=external_sources.daily_prog_affinity.program_id
join backend.broadcast as bb
on bb.PROGRAM_ID = bp.ID
join free_channel as fc
on bb.CHANNEL_ID = fc.CHANNEL_ID
where REF_PROGRAM_CATEGORY_ID = 1 and START_AT >= current_date and START_AT < current_date + 7
order by total_celeb_points desc
```

For most watched programs : 
```

select backend.program.ID, backend.program.TITLE, affinity, round(sum(dw.fact_watch.DURATION) / 3600, 0) as total_duration 
from dw.fact_watch 
join backend.program on program_id = id
left join external_sources.daily_prog_affinity
on backend.program.ID=external_sources.daily_prog_affinity.program_id
join backend.broadcast
on backend.program.ID=backend.broadcast.PROGRAM_ID
where dw.fact_watch.real_start_at > current_date - 14 and ref_program_category_id in (1) and affinity like '%Thrillers & Policiers%' and start_at > current_date 
group by backend.program.ID, backend.program.TITLE, affinity
order by total_duration desc;
```