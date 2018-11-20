#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gitlab
import sys
import json
from mattermostdriver import Driver as mtd

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
        for group in gl.groups.list():
            gitlab_groups_names.append(group.full_name.split('/')[len(group.full_name.split('/')) - 1].strip())
            gitlab_group = {"name": group.full_name.split('/')[len(group.full_name.split('/')) - 1].strip(),
                            "members": []}
            for member in group.members.list():
                user = gl.users.get(member.id)
                gitlab_group['members'].append(user.username)
            gitlab_groups.append(gitlab_group)
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
                    print('|  |  |- User %s present in GitLab but not in Mattermost, updating Mattermost' % g_member)
                    u = mt.users.get_user_by_username(username=g_member)
                    mt.teams.add_user_to_team(team_id=g['id'], options={'team_id': g['id'], 'user_id': u['id']})
                else:
                    print('|  |  |- User %s present in GitLab and Mattermost, skipping' % g_member)
            print('|- Done')
        print('Done.')

        if config['cleanup_mattermost']:
            print('Cleaning Mattermost membership')
            for m_group in mattermost_groups:
                print('|- Workgin on %s.' % m_group['name'])
                if m_group['name'] not in gitlab_groups_names:
                    print('|  |  |- %s not present in GitLab, is this an error? Skipping.' % m_group['name'])
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
