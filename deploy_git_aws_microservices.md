# Deploying a Python Program as a Microservice in AWS: Step-by-Step Guide

This document provides a comprehensive step-by-step guide to deploying a Python program as a microservice on AWS, based on what worked during our learning process. We will cover everything from creating a Python script to containerizing it, pushing the Docker image to AWS, and deploying it using Amazon ECS with Fargate.

## Step 1: Create a Simple Python Program

1. **Create a Project Folder**: Create a folder named `BasicMicroserviceProject` on your local machine.

2. **Create Files**:

   - `main.py`: This is the main Python script.
   - `config.yaml`: A configuration file.
   - `requirements.txt`: This file lists the dependencies for the program.

   The folder structure should look like this:

   ```
   BasicMicroserviceProject/
   ├── main.py
   ├── config.yaml
   └── requirements.txt
   ```

3. **Write the Python Script (`main.py`)**:

   ```python
   import yaml

   def load_config(config_path):
       with open(config_path, 'r') as file:
           config = yaml.safe_load(file)
       return config

   def main():
       # Load configuration
       config = load_config('config.yaml')
       message = config.get('message', 'Hello, World!')
       
       # Print the message
       print(f"Message from config: {message}")

   if __name__ == "__main__":
       main()
   ```

4. **Write the Configuration File (`config.yaml`)**:

   ```yaml
   message: "Hello from my microservice!"
   ```

5. **Write the Requirements File (`requirements.txt`)**:

   ```
   pyyaml
   ```

6. **Test the Program**:

   - Run the script locally to ensure it works:
     ```bash
     python main.py
     ```
   - You should see: `Message from config: Hello from my microservice!`

## Step 2: Create a Dockerfile

1. **Create a Dockerfile** in the `BasicMicroserviceProject` folder.

2. **Dockerfile Content**:

   ```dockerfile
   # Use a lightweight Python image as the base image
   FROM python:3.10-slim

   # Set the working directory inside the container
   WORKDIR /app

   # Copy the requirements file to the container
   COPY requirements.txt /app

   # Install the required dependencies
   RUN pip install --upgrade pip
   RUN pip install -r requirements.txt

   # Copy the rest of the application code to the container
   COPY . /app

   # Set the command to run the script
   CMD ["python", "main.py"]
   ```

## Step 3: Push Docker Image to AWS ECR Using CodeBuild

Since Docker couldn't be run locally, we used AWS CodeBuild to build the Docker image and push it to ECR.

1. **Create an ECR Repository**:

   - Go to the AWS Management Console, search for **ECR**, and create a new repository named `basic_microservice_repo`.

2. **Service Role Permissions**:

   - Make sure the IAM role used by CodeBuild has the necessary permissions to interact with Amazon ECR.
      - You may need to attach the following managed policies to your role:
         - AmazonEC2ContainerRegistryFullAccess
         - AmazonS3FullAccess
         - CloudWatchLogsFullAccess

3. **Create `buildspec.yml`**:

   - Create a `buildspec.yml` file in your `BasicMicroserviceProject` folder:

   ```yaml
   version: 0.2

   phases:
     pre_build:
       commands:
         - echo Logging in to Amazon ECR...
         - aws --version
         - aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.<your-region>.amazonaws.com
         - REPOSITORY_URI=<your-account-id>.dkr.ecr.<your-region>.amazonaws.com/basic_microservice_repo
     build:
       commands:
         - echo Build started on `date`
         - echo Building the Docker image...
         - docker build -t basic_microservice_image .
         - docker tag basic_microservice_image:latest $REPOSITORY_URI:latest
     post_build:
       commands:
         - echo Build completed on `date`
         - echo Pushing the Docker image...
         - docker push $REPOSITORY_URI:latest
         - echo Docker image successfully pushed

   artifacts:
     files:
       - '**/*'
   ```

   Replace `<your-region>` and `<your-account-id>` with your AWS region and account ID.

4. **Set Up CodeBuild Project**:

   - Go to **CodeBuild** in AWS Console, create a new project, and link it to your source code (e.g., GitHub or S3 bucket).
   - Use the **buildspec.yml** you created.
   - Make sure the environment image supports Docker.

5. **Run CodeBuild**:

   - Run the CodeBuild project, and it will build the Docker image and push it to ECR.

## Step 4: Deploy the Docker Container Using AWS ECS (Elastic Container Service)

1. **Create an ECS Cluster**:

   - Go to **ECS** in AWS Console and create a new cluster.
   - Use **Fargate** to create a serverless cluster (`basic_microservice_cluster`).

2. **Register a Task Definition**:

   - Go to **Task Definitions** and create a new task definition using **Fargate**.
   - **Task Definition Name**: `basic_microservice_task`.
   - **Container Definitions**:
     - **Container Name**: `basic_microservice`.
     - **Image**: Use the ECR URI of the Docker image.
     - **Memory and CPU**: Set to appropriate values, such as `256 MiB` and `256` CPU units.
     - **Logging**: Configure to use **CloudWatch Logs**.

3. **Run the Task**:

   - Go to your ECS cluster (`basic_microservice_cluster`) and click **Run Task**.
   - Select **Fargate** and use the task definition (`basic_microservice_task`).
   - Configure **network settings** (e.g., VPC, subnets, and security groups).

4. **Verify the Task**:

   - Once the task is running, go to **CloudWatch Logs** to verify that the output (`Message from config: Hello from my microservice!`) appears.

## Step 5: Set Up a Schedule (Optional)

1. **Use Amazon EventBridge** to run the ECS task on a schedule (e.g., daily or weekly).
   - Create a new rule with a schedule expression.
   - Set the target as your ECS task to automate execution.

## Rollback Steps

### Step 1: Delete the ECS Cluster
- **Navigate to the ECS Console** in AWS.
- Find the cluster (`basic_microservice_cluster`) you created.
- **Select the cluster**, and click on **"Delete Cluster"**.
- This action will terminate any running tasks and remove the cluster.

### Step 2: Deregister the Task Definition
- **Navigate to Task Definitions** in the ECS Console.
- Locate the task definition (`basic_microservice_task`).
- **Select the task definition**, and choose **"Actions"** > **"Deregister"**.
- Deregistering the task definition will prevent any future tasks from being launched using this version.

### Step 3: Delete the ECR Repository
- **Go to the Amazon ECR Console**.
- Find the repository (`basic_microservice_repo`) you created.
- **Select the repository**, and click on **"Delete"**.
- Make sure to confirm that you want to delete the repository along with any images stored in it.

### Step 4: Delete CodeBuild Project
- **Navigate to CodeBuild Console**.
- Find the project you created to build the Docker image.
- **Select the project**, and click on **"Delete"**.
- This will remove the CodeBuild configuration, and you won't be billed for this resource anymore.

### Step 5: Delete CloudWatch Log Groups (Optional)
- **Go to the CloudWatch Console** and navigate to **Logs**.
- Look for the **log group** associated with the ECS tasks (e.g., `/ecs/basic_microservice_logs`).
- **Select the log group**, and click on **"Delete Log Group"**.
- This will clean up any log data stored from the running tasks.

### Step 6: Delete IAM Roles (Optional)
- If you created any **IAM roles** specifically for ECS or CodeBuild that aren't being used elsewhere:
  - **Go to the IAM Console**.
  - **Select the role**, and ensure that it's not being used by other services.
  - **Delete the role** to ensure that there are no lingering permissions.

### Step 7: Clean Up Local Resources
- **Delete the Project Folder** (`BasicMicroserviceProject`) from your local machine if you no longer need it.
- This includes `main.py`, `config.yaml`, `requirements.txt`, `Dockerfile`, and `buildspec.yml`.

## Summary

1. **Create a Python script**, configuration file, and requirements file.
2. **Write a Dockerfile** and push the Docker image to ECR using CodeBuild.
3. **Deploy the container** in an ECS cluster using Fargate.
4. **Run and monitor** the microservice using ECS and CloudWatch Logs.
5. Optionally, use **EventBridge** to schedule the task.
6. **Rollback Steps**: Delete the ECS cluster, deregister the task definition, delete the ECR repository, delete the CodeBuild project, delete CloudWatch logs, delete IAM roles, and clean up local resources.

With these steps, your Python microservice is now deployed in AWS, running serverlessly in ECS, and can be easily managed and scaled as needed. The rollback steps ensure that all resources are safely cleaned up if needed.

