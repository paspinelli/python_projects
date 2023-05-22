import requests
import pandas as pd
import logging
import threading
from queue import Queue
from  collections import defaultdict

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


class BitbucketGetter:
    def __init__(self, key, secret, refresh_token=None):
        self.key = key
        self.secret = secret
        self.refresh_token = refresh_token
        self.logger = logging
        self.logger.info('Starting BitbucketGetter')
        self.base_url = 'https://api.bitbucket.org/2.0'
        self.old_base_url = 'https://api.bitbucket.org/1.0'
        self.threaded_perms_dict = defaultdict(list)
        if refresh_token:
            self.headers = {
                'Authorization': f'Bearer {self.get_access_token()}'}
            self.execute_query = self.execute_query_token
        else:
            self.execute_query = self.execute_query_basic
        self.current_user = self.execute_query('user')['nickname']

    def execute_query_basic(self, resource, query='', page='', old_api=False):
        base_url = self.base_url if not old_api else self.old_base_url
        url = f'{base_url}/{resource}/{query}{page}'
        try:
            return requests.get(url, auth=(self.key, self.secret)).json()
        except:
            self.logger.info('Check your access details')

    def execute_query_token(self, resource, query='', page='', old_api=False):
        base_url = self.base_url if not old_api else self.old_base_url
        url = f'{base_url}/{resource}/{query}{page}'
        try:
            return requests.get(url, headers=self.headers).json()
        except:
            self.logger.info('Check your access details')

    def get_access_token(self):
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }

        return requests.post('https://bitbucket.org/site/oauth2/access_token', data=data, auth=(self.key, self.secret)).json()['access_token']

    def get_workspaces(self, response_workspace, res_type='slug'):
        return [i[res_type] for i in response_workspace if self.current_user in self.get_workspace_owners(i[res_type])]

    def get_workspace_owners(self, workspace):
        return [i['user']['nickname'] for i in self.execute_query('workspaces', f'{workspace}/members?q=permission="owner"')['values']]

    def get_repositories(self, workspace, res_type='slug', limit_page=999):
        page = 1
        self.logger.info(f"Getting repositories from page {page}")
        current_repos = self.execute_query(
            'repositories', workspace, page=f"?page={page}")
        repos_pages = [current_repos]
        while current_repos.get('next', None) and page <= limit_page:
            page -=- 1
            self.logger.info(f"Getting repositories from page {page}")
            current_repos = self.execute_query('repositories', workspace, page=f"?page={page}")
            repos_pages.append(current_repos)

        return [(i[res_type], i['project']['key'], i['project']['name'])
                for repos_page in repos_pages for i in repos_page['values']]

    def get_permissions(self, workspace, repos):
        self.logger.info(f"Processing workspace: {workspace}")

        perms_list = list()
        for repo, project_key, project_name in repos:
            res = self.get_repo_permissions(workspace, repo)
            users_group = self.get_group_members(workspace, repo)
            for user in res:
                nick = user['user']['nickname']
                perms_list.append(
                    {
                        'user_name': nick,
                        'user_nickname': user['user']['nickname'],
                        'project_key': project_key,
                        'project_name': project_name,
                        'repo': repo,
                        'repo_full_name': user['repository']['full_name'],
                        'group': users_group.get(nick, 'No group'),
                        'permission': user['permission']
                    }
                )
        return perms_list

    def get_permissions_thread(self, workspace, repo):
        repo, project_key, project_name = repo
        res = self.get_repo_permissions(workspace, repo)
        users_group = self.get_group_members(workspace, repo)
        for user in res:
            nick = user['user']['nickname']
            self.threaded_perms_dict[workspace].append(
                {
                    'user_name': nick,
                    'user_nickname': user['user']['nickname'],
                    'project_key': project_key,
                    'project_name': project_name,
                    'repo': repo,
                    'repo_full_name': user['repository']['full_name'],
                    'group': users_group.get(nick, 'No group'),
                    'permission': user['permission']
                }
            )

    def get_repo_permissions(self, workspace, repo):
        # According to bitbucket.com api description 'teams' resource is depcrecated
        # this may no work in a near future
        self.logger.info(f'Getting permissions for each user from repository: {repo}')
        return self.execute_query('teams', f'{workspace}/permissions/repositories/{repo}')['values']

    def get_group_members(self, workspace, repo):
        # Returns {'member_nickname': 'group_name'}
        self.logger.info(f'Getting groups for each repo {repo} members')
        self.logger.warning('We are using the old API!')
    
        groups = self.execute_query('group-privileges', f'{workspace}/{repo}', old_api=True)
        res = {}
        for group in groups:
            group = group['group']
            for member in group['members']:
                res[member['nickname']] = group['slug']

        return res


    def save_report(self, perms_dict, format_='csv'):
        self.logger.info(f'Saving report in {format_} format')

        for workspace, data in perms_dict.items():
            if format_ == 'csv':
                pd.DataFrame(data).to_csv(f'{workspace}.csv', index=False)
            else:
                pd.DataFrame(data).to_excel(f'{workspace}.xlsx', index=False)

    def generate_report(self, save_report=True, format_='csv'):
        self.logger.warning("Deprecated... use generate_report_multithread() instead")
        self.logger.info('Generating report..')

        workspaces = self.get_workspaces(
            self.execute_query('workspaces')['values'])
        perms_dict = dict()
        for workspace in workspaces:
            repos = self.get_repositories(workspace)
            perms = self.get_permissions(workspace, repos)
            perms_dict[workspace] = perms

        if save_report:
            self.save_report(perms_dict, format_=format_)

        return perms_dict


    def manage_queue(self):
        """Manages the url_queue and calls the make request function"""
        while True:
            # Stores the (workspace, repo) tuple and removes it from the queue so no 
            # other threads will use it. 
            workspace, repo = self.request_queue.get()

            # Calls function
            self.get_permissions_thread(workspace, repo)

            # Tells the queue that the processing on that task is complete.
            self.request_queue.task_done()

    def generate_report_multithread(self, save_report=True, format_='csv', n_threads=30):
        self.logger.info('Generating multithreaded report..')
        self.request_queue = Queue()
        if n_threads > 100:
            self.logger.warning(f"You're using too much threads, it may cause missing rows")

        for _ in range(n_threads):
            t = threading.Thread(target=self.manage_queue)
            # Makes the thread a daemon so it exits when the program finishes.
            t.daemon = True
            t.start()

        workspaces = self.get_workspaces(self.execute_query('workspaces')['values'])
        for workspace in workspaces:
            repos = self.get_repositories(workspace)
            for repo in repos:
                self.request_queue.put((workspace, repo))
        
        self.request_queue.join()

        if save_report:
            self.save_report(self.threaded_perms_dict, format_=format_)

        return self.threaded_perms_dict



if __name__ == "__main__":
    key = ''  # USERNAME
    secret = '' # PASS
    x = BitbucketGetter(key, secret)
    # x.generate_report(format_='csv') # DEPRECATED
    x.generate_report_multithread(format_='excel', n_threads=50)
