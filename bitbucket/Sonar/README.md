# Bitbucket & SonarCloud

[![N|Solid](https://pbs.twimg.com/profile_images/543075498620760064/2rWxJDN5_400x400.jpeg)]()

### Requirements

* Install Node & NPM
* Macos >> https://nodesource.com/blog/installing-nodejs-tutorial-mac-os-x/
* Linux >> https://ostechnix.com/install-node-js-linux/
* Windows >> https://phoenixnap.com/kb/install-node-js-npm-on-windows

## Env variables (.env file)

* <SONAR_TOKEN> 		-> This will be the Token ID from SONAR Admin (My Account -> Security -> Generate Token)
* <BITBUCKET_USER> 		-> Email or username from bitbucket account
* <BITBUCKET_PASS> 		-> Password from bitbucket account
* <BITBUCKET_WORKSPACE> -> Workspace from bitbucket to review

## How to run it
```sh
$ cd folder
$ npm install & npm start
```

## Output

The `output.csv` file in the ROOT of the project with the information needed.

This will be prompting ONLY the projects that has SONAR analysis done, the other ones will have empty data.

This might take a while to process depending on the projects, and also remind that the algorithm is not fully performance at the moment as it was a POC.

### Fields Description

| Field                          | Description                                                 |
| ------------------------------ | ----------------------------------------------------------- |
| Workspace                      | Workspace name from Bitbucket.                              |
| Project                        | Project name from Bitbucket.                                |
| Repository                     | Repository name from Bitbucket.                             |
| Repository ID                  | UUID from the repository.                                   |
| Pull Request enabled?          | Indicates if pull request are enabled. Default value: "yes" |
| Default Pull Request Approvers | List of default users to approve a pull request.            |
| Last Commit                    | Date of the last commit from the main branch.               |
| Sonar ID                       | Project key from Sonar.                                     |
| Open Issues Total              | The total number of open issues.                            |
| Open Bugs Total                | The total number of open issues with type "BUG".            |
| Blocker Bugs                   | The total number of bugs with BLOCKER severity.             |
| Critical Bugs                  | The total number of bugs with CRITICAL severity.            |
| Major Bugs                     | The total number of bugs with MAJOR severity.               |
| Info Bugs                      | The total number of bugs with INFO severity.                |
| Minor Bugs                     | The total number of bugs with MINOR severity.               |
| Open Vulnerabilities Total     | The total number of open issues with type "VULNERABILITY".  |
| Blocker Vulnerabilities        | The total number of vulnerabilities with BLOCKER severity.  |
| Critical Vulnerabilities       | The total number of vulnerabilities with CRITICAL severity. |
| Major Vulnerabilities          | The total number of vulnerabilities with MAJOR severity.    |
| Info Vulnerabilities           | The total number of vulnerabilities with INFO severity.     |
| Minor Vulnerabilities          | The total number of vulnerabilities with MINOR severity.    |
| Open Code Smells Total         | The total number of open issues with type "CODE_SMELL".     |
| Blocker Code Smells            | The total number of code smells with BLOCKER severity.      |
| Critical Code Smells           | The total number of code smells with CRITICAL severity.     |
| Major Code Smells              | The total number of code smells with MAJOR severity.        |
| Info Code Smells               | The total number of code smells with INFO severity.         |
| Minor Code Smells              | The total number of code smells with MINOR severity.        |
| owasp a1                       | Injection                                                   |
| owasp a2                       | Broken Authentication                                       |
| owasp a3                       | Sensitive Data Exposure                                     |
| owasp a4                       | XML External Entities (XXE)                                 |
| owasp a5                       | Broken Access Control                                       |
| owasp a6                       | Security Misconfiguration                                   |
| owasp a7                       | Cross-Site Scripting (XSS)                                  |
| owasp a8                       | Insecure Deserialization                                    |
| owasp a9                       | Using Components with Known Vulnerabilities                 |
| owasp a10                      | Insufficient Logging & Monitoring                           |
| Last Issue                     | Creation date of the newest issue.                          |
| Last Scan                      | Date from the last analysis with Sonar.                     |

