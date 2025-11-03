# 225lab4-2

This is an extension of the persistent flask/sqlite3 app and adds in generated data and tests that it has been added with selenium.  Deploys to your __ClusterIP__  test data is added, and then it is deleted.  Please note: This requires persistence to be set up on your cluster!  Please do not attempt until it has been added!

1) Create a new blank repository in your GitHub account using the lab name above.
2) Copy the URL of this repository and paste it into your repository.
3) View each file, and make changes where it is commented.  The index.html page is in the templates directory.  You will also edit the Jenkinsfile, deployment-dev.yaml (your nfs directory and the container image), deployment-prod.yaml (your nfs directory, the container image and your load balancer IP) and test_html_elements.py (your cluster IP).
4) Start your screencapture. Demonstrate your changes to the code in your video, and show the resulting web page.
6) Run your pipeline.
7) Refresh your web page during the test cycle AFTER Deploy Dev Environment, then again AFTER Reset DB, then again AFTER Run Acceptance Tests, and Finally AFTER Remove Test Data. Talk about what happened to the page as you refreshed it.
