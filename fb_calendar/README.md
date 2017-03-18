# fb_calendar
[![Build Status](https://travis-ci.org/akellehe/fb_calendar.svg?branch=master)](https://travis-ci.org/akellehe/fb_calendar)

## Development

### Ansible Vault 

We use [ansible vault](http://docs.ansible.com/ansible/playbooks_vault.html) to encrypt application secrets. At the moment we only have development versions of secret variables. When we get stage up and running we'll update our playbooks to be environment specific (typically with a secrets.stage.yml, secrets.prod.yml, etc).  

We need to do a little research to figure out how to encrypt vault files for each developer. Our secrets at the moment can be found at `deploy/roles/fb_calendar_api/vars/main.yml`. We should deprecate this and call it `secrets.yml` instead of `main.yml`. 

If you want to get started ensuring we encrypt for each developer I think we just need to research _vault keys_. For now; try running the command:

```bash
ansible-vault edit deploy/roles/fb_calendar_api/vars/main.yml
```
For the vault password just ask Andrew.

### Spinning up your virtual environment

This project uses Virtual Machines to ensure consistency across and speed to get dev enviroments up and running.

You'll need to install [VirtualBox](https://www.virtualbox.org/) and vagrant. Make sure your versions are greater than or equal to 

 * vagrant 1.8.6
 * ansible 1.9.4
 * VirtualBox 5.0.20

Once you have these installed you should clone the repository to `/src/fb_calendar` on your physical machine:

  1. Create a `/src` directory; `sudo mkdir /src && sudo chown [your username]:[your group] /src`_
  2. Clone the repository to that directory: `git clone git@github.com:akellehe/fb_calendar.git`_ 

Once you've got a copy of the project in the correct directory you should `cd` there and spin up the virtual machine:

```
cd /src/fb_calendar && vagrant up
```

In a couple minutes you'll have a full functional linux box running on your machine with the API installed as well as a fully configured, migrated postgres database.

## Administration

We use `daemontools`/`svc` to manage services we write. At the moment there are two services; the web application itself at `/service/webapp-0` and a daemon 
that continually updates database entries with the latest events `/service/event_scraper-0`.

### Checking Service Status 

You can check how long it's been running with `svstat`, e.g.

```
sudo svstat /service/webapp-0
```

### Starting, Stopping, and restarting services

You can kill that service using `svc`

```
sudo svc -k /service/webapp-0
```

You can bring it down if you pass `-d` instead of `-k`, and back up if you pass `-u`.

### Inspecting Logs

You can use `tail` like you normally would to see what's going on in the project logs. We always prefer `logger.info` to `print` statements.

```
tail -f /service/webapp-0/log/current
```

## Test/Debug Cycles

For backend development _test driven development_ is preferred. This means you should have no need to continually stop/restart services. Tests should be written and run to satisfy application feature requirements. When they pass the feature is done.

For frontend development; we'll get a 'watchdog' together to look for frontend changes, but in the meantime you have to re-deploy to the VM for each change. 

## Deployment Process

Each feature can be deployed on it's own by the developer. We have no release schedule for backend features. The process for deployment is:
 
  1. Create a branch for your feature. Changes go there _only_.
  2. Before submitting your branch for review you MUST run all test, and QA your own feature. 
  3. When your branch is ready for review; _squash your commits_. 
  4. Assign reviewers on github. Send the a note to let them know they've been assigned since we all miss github emails.
  5. When your code has been reviewed the reviewer will "approve" the feature.
  6. Any changes require a re-review. _Do not squash the branch again until it is ready for merge_
  7. After the branch passes review you should QA it once more, and run all the tests again. 
  8. When you're sure your feature is ready to go to production; squash your commits and merge into master.
  9. Deploy _only your merged commit_ to staging. Do not deploy `master`, use the commit #.
  10. QA your feature again on stage. Run through a 'sanity check'.
  11. Deploy _your commit_ to production.
  12. Verify your feature on production.
   
If something goes wrong in this process; you should roll back. This means:
  
  1. Merge a `revert` commit for your commit into master.
  2. Start at step 9. above.

### Deploying

The actual command to deploy to dev is just 

```bash
vagrant up
```

To reprovision with just ansible you can use

```bash
vagrant provision --provision-with ansible
```

To deploy to stage you can use (from the working directory)

```bash
ansible-playbook deploy/fb_calendar.yml -i deploy/inventories/stage.ini -vvv -e env=stage
```

You should have your vault password stored in `~/.vault_password` 


### Android

Android development is done through [Android Studio](https://developer.android.com/studio/index.html), which is available on all platforms. Download and install it. The [tutorials](https://developer.android.com/studio/intro/index.html) are great but skip ahead if you feel like it.

You should be able to open the subdirectory `/src/fb_calendar/WakeAndShake-android` in Android Studio. You'll need to add an [emulator](https://developer.android.com/studio/run/emulator.html).

Unfortunately running Android VMs is not possible alongside other (vagrant) VMs on the same machine. For that reason we'll need to do Android development against the staging version of our backend. Make sure your (backend) vagrant machine is destroyed before trying to run the emulator or you'll get annoying messages about how the emulator was killed each time.
