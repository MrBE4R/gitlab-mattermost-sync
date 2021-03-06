#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gitlab
import sys
import json
from mattermostdriver import Driver as mtd
from time import sleep

if __name__ == "__main__":
    print('Initializing gitlab-ldap-sync.')
    config = None
    with open('config.json') as f:
        config = json.load(f)
    if config is not None:
        print('Done.')
        print('Connecting to GitLab')
        if config['gitlab']['api']:
            gl = None
            if not config['gitlab']['private_token'] and not config['gitlab']['oauth_token']:
                print('You should set at least one auth information in config.json, aborting.')
            elif config['gitlab']['private_token'] and config['gitlab']['oauth_token']:
                print('You should set at most one auth information in config.json, aborting.')
            else:
                if config['gitlab']['private_token']:
                    gl = gitlab.Gitlab(url=config['gitlab']['api'], private_token=config['gitlab']['private_token'])
                elif config['gitlab']['oauth_token']:
                    gl = gitlab.Gitlab(url=config['gitlab']['api'], oauth_token=config['gitlab']['oauth_token'])
                else:
                    gl = None
                if gl is None:
                    print('Cannot create GitLab object, aborting.')
                    sys.exit(1)
            gl.auth()
            print('Done.')
        else:
            print('GitLab API is empty, aborting.')
            sys.exit(1)

        print('Connecting to Mattermost')
        if config['mattermost']['api']:
            if not config['mattermost']['private_token'] and not config['mattermost']['username']:
                print('You should set at least one auth information in config.json, aborting.')
            elif config['mattermost']['private_token'] and config['mattermost']['username']:
                print('You should set at most one auth information in config.json, aborting.')
            else:
                if config['gitlab']['private_token']:
                    mt = mtd({
                        'url': config['mattermost']['api'],
                        'token': config['mattermost']['private_token'],
                        'scheme': 'https',
                        'port': 443,
                        'timeout': 30,
                        'debug': False
                    })
                elif config['mattermost']['username'] and config['mattermost']['password']:
                    mt = mtd({
                        'url': config['mattermost']['api'],
                        'login_id': config['mattermost']['username'],
                        'password': config['mattermost']['password'],
                        'scheme': 'https',
                        'port': 443,
                        'timeout': 30,
                        'debug': False
                    })
                else:
                    mt = None

                if mt is None:
                    print('Cannot create Mattermost object, aborting.')
                    sys.exit(1)
            mt.login()
            print('Done.')
        else:
            print('Mattermost API is empty, aborting.')
            sys.exit(1)

        print('Getting all groups from GitLab.')
        gitlab_groups = []
        gitlab_groups_names = []
        for group in gl.groups.list(all=True):
            gitlab_groups_names.append(group.full_name.split('/')[len(group.full_name.split('/')) - 1].strip())
            gitlab_group = {"name": group.full_name.split('/')[len(group.full_name.split('/')) - 1].strip(), "members": []}
            for member in group.members.list(all=True):
                user = gl.users.get(member.id)
                gitlab_group['members'].append(user.username)
            gitlab_groups.append(gitlab_group)
        print('Done.')

        print('Getting all projects from GitLab.')
        gitlab_projects = []
        gitlab_projects_names = []
        for project in gl.projects.list(all=True):
            gitlab_projects_names.append(project.name.split('/')[len(project.name.split('/')) - 1].strip())
            gitlab_project = {"name": project.name.split('/')[len(project.name.split('/')) - 1].strip(), "members": []}
            for member in project.members.list(all=True):
                user = gl.users.get(member.id)
                gitlab_project['members'].append(user.username)
            gitlab_projects.append(gitlab_project)
        print('Done.')

        print('Getting all groups from Mattermost.')
        mattermost_groups = []
        mattermost_groups_names = []
        for group in mt.teams.get_teams():
            mattermost_group = {"name": group['display_name'], "team_name": group['name'], "members": []}
            for users in mt.teams.get_team_members(group['id']):
                u = mt.users.get_user(users['user_id'])
                mattermost_group['members'].append(u['username'])
            mattermost_groups_names.append(group['display_name'])
            mattermost_groups.append(mattermost_group)
        print('Done.')

        print('Importing groups from GitLab')
        for g_group in gitlab_groups:
            print('|- Workgin on %s.' % g_group['name'])
            if g_group['name'] not in mattermost_groups_names:
                print('|  |- %s does not exist in Mattermost, creating.' % g_group['name'])
                g = mt.teams.create_team(options={
                    'name': ''.join([s for s in g_group['name'] if str.isalnum(s)]).lower(),
                    'display_name': g_group['name'],
                    'type': 'I'
                })
                print('Done.')

                mattermost_groups = []
                mattermost_groups_names = []
                for group in mt.teams.get_teams():
                    mattermost_group = {"name": group['display_name'], "team_name": group['name'], "members": []}
                    for users in mt.teams.get_team_members(group['id']):
                        u = mt.users.get_user(users['user_id'])
                        mattermost_group['members'].append(u['username'])
                    mattermost_groups_names.append(group['display_name'])
                    mattermost_groups.append(mattermost_group)
            else:
                print('|  |- %s already not exist in Mattermost, skipping creation.' % g_group['name'])
                g = mt.teams.get_team_by_name(name=''.join([s for s in g_group['name'] if str.isalnum(s)]).lower())

            for g_member in g_group['members']:
                if g_member not in mattermost_groups[mattermost_groups_names.index(g_group['name'])]['members']:
                    u = []
                    print('|  |  |- User %s present in GitLab but not in Mattermost, updating Mattermost' % g_member)
                    if str(g_member):
                        u = mt.users.search_users({'term': str(g_member)})
                    if len(u) > 0:
                        u = mt.users.get_user_by_username(username=g_member)
                        mt.teams.add_user_to_team(team_id=g['id'], options={'team_id': g['id'], 'user_id': u['id']})
                    else:
                        print('|  |  |  |- User %s does not have a mattermost account, skipping.' % g_member)
                else:
                    print('|  |  |- User %s present in GitLab and Mattermost, skipping' % g_member)
                sleep(0.3)

            print('|- Done')
        print('Done.')

        print('Importing project from GitLab')
        for g_project in gitlab_projects:
            print('|- Workgin on %s.' % g_project['name'])
            if g_project['name'] not in mattermost_groups_names:
                print('|  |- %s does not exist in Mattermost, creating.' % g_project['name'])
                g = mt.teams.create_team(options={
                    'name': ''.join([s for s in g_project['name'] if str.isalnum(s)]).lower(),
                    'display_name': g_project['name'],
                    'type': 'I'
                })
                print('Done.')

                mattermost_groups = []
                mattermost_groups_names = []
                for group in mt.teams.get_teams():
                    mattermost_group = {"name": group['display_name'], "team_name": group['name'], "members": []}
                    for users in mt.teams.get_team_members(group['id']):
                        u = mt.users.get_user(users['user_id'])
                        mattermost_group['members'].append(u['username'])
                    mattermost_groups_names.append(group['display_name'])
                    mattermost_groups.append(mattermost_group)
            else:
                print('|  |- %s already not exist in Mattermost, skipping creation.' % g_project['name'])
                g = mt.teams.get_team_by_name(name=''.join([s for s in g_project['name'] if str.isalnum(s)]).lower())
            for g_member in g_project['members']:
                if g_member not in mattermost_groups[mattermost_groups_names.index(g_project['name'])]['members']:
                    u = []
                    print('|  |  |- User %s present in GitLab but not in Mattermost, updating Mattermost' % g_member)
                    if str(g_member):
                        u = mt.users.search_users({'term': str(g_member)})
                    if len(u) > 0:
                        u = mt.users.get_user_by_username(username=g_member)
                        mt.teams.add_user_to_team(team_id=g['id'], options={'team_id': g['id'], 'user_id': u['id']})
                    else:
                        print('|  |  |  |- User %s does not have a mattermost account, skipping.' % g_member)
                else:
                    print('|  |  |- User %s present in GitLab and Mattermost, skipping' % g_member)
                sleep(0.3)
            print('|- Done')
        print('Done.')

        if config['cleanup_mattermost']:
            print('Cleaning Mattermost membership')
            for m_group in mattermost_groups:
                print('|- Workgin on %s.' % m_group['name'])
                if m_group['name'] not in gitlab_groups_names:
                    if m_group['name'] not in gitlab_projects_names:
                        print('|  |  |- Project or group %s not present in GitLab, is this an error? Skipping.' % m_group['name'])
                    else:
                        g = mt.teams.get_team_by_name(name=''.join([s for s in m_group['name'] if str.isalnum(s)]).lower())
                        for m_member in m_group['members']:
                            if m_member not in gitlab_projects[gitlab_projects_names.index(m_group['name'])]['members']:
                                print('|  |  |- User %s present in Mattermost but not in GitLab, updating Mattermost' % m_member)
                                u = mt.users.get_user_by_username(username=m_member)
                                mt.teams.remove_user_from_team(team_id=g['id'], user_id=u['id'])
                            else:
                                print('|  |  |- User %s present in GitLab and Mattermost, skipping' % m_member)
                else:
                    g = mt.teams.get_team_by_name(name=''.join([s for s in m_group['name'] if str.isalnum(s)]).lower())
                    for m_member in m_group['members']:
                        if m_member not in gitlab_groups[gitlab_groups_names.index(m_group['name'])]['members']:
                            print('|  |  |- User %s present in Mattermost but not in GitLab, updating Mattermost' % m_member)
                            u = mt.users.get_user_by_username(username=m_member)
                            mt.teams.remove_user_from_team(team_id=g['id'], user_id=u['id'])
                        else:
                            print('|  |  |- User %s present in GitLab and Mattermost, skipping' % m_member)
                print('|- Done.')
            print('Done.')

    else:
        print('Could not load config.json, check if the file is present.')
        print('Aborting.')
        sys.exit(1)
