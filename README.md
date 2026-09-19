# Manara Project --- AWS Cloud-Native CI/CD Tasks API

A production-inspired cloud deployment project that demonstrates how to
build, containerize, deploy, and operate a FastAPI application using AWS
managed services.

The project implements an automated CI/CD workflow:

``` text
GitHub
   ↓
AWS CodePipeline
   ↓
AWS CodeBuild
   ↓
Amazon ECR
   ↓
Amazon ECS Fargate
   ↓
Application Load Balancer
   ↓
FastAPI Application
```

The application uses Amazon RDS for persistent PostgreSQL data, Amazon
CloudWatch for operational logs, Amazon S3 for log-file storage, and AWS
Secrets Manager for database credentials.

------------------------------------------------------------------------

## Table of Contents

-   [Project Overview](#project-overview)
-   [Project Goals](#project-goals)
-   [Architecture](#architecture)
-   [AWS Services and Why They Are
    Used](#aws-services-and-why-they-are-used)
-   [Application Features](#application-features)
-   [Repository Structure](#repository-structure)
-   [CI/CD Workflow](#cicd-workflow)
-   [Networking and Security](#networking-and-security)
-   [Infrastructure as Code](#infrastructure-as-code)
-   [Configuration](#configuration)
-   [Deployment Overview](#deployment-overview)
-   [API Endpoints](#api-endpoints)
-   [Observability and Logging](#observability-and-logging)
-   [Cost Considerations](#cost-considerations)
-   [Security Considerations](#security-considerations)
-   [Limitations and Future
    Improvements](#limitations-and-future-improvements)
-   [Cleanup](#cleanup)
-   [Learning Outcomes](#learning-outcomes)

------------------------------------------------------------------------

## Project Overview

**Manara Project** is a containerized Tasks API built with **FastAPI**
and deployed on **Amazon ECS Fargate**.

The project is designed to demonstrate practical DevOps and cloud
engineering concepts, including:

-   Containerization with Docker
-   Continuous integration and continuous delivery
-   AWS infrastructure provisioning with CloudFormation
-   Load balancing
-   Serverless container orchestration
-   PostgreSQL database integration
-   IAM roles and least-privilege permissions
-   Centralized application logging
-   Secret management
-   VPC networking and security groups

The project uses AWS-native CI/CD services rather than GitHub Actions.

------------------------------------------------------------------------

## Project Goals

The main goals of this project are to:

1.  Build a simple REST API using FastAPI.
2.  Package the application as a Docker image.
3.  Store and version container images in Amazon ECR.
4.  Automatically build and deploy new application versions through AWS
    CodePipeline.
5.  Run the application on ECS Fargate without managing EC2 servers.
6.  Store application data in Amazon RDS PostgreSQL.
7.  Expose the application through an Application Load Balancer.
8.  Send runtime logs to Amazon CloudWatch Logs.
9.  Store application log files in Amazon S3.
10. Manage database credentials using AWS Secrets Manager.
11. Define the AWS infrastructure as code using AWS CloudFormation.

------------------------------------------------------------------------

## Architecture

### Solution Architecture Diagram

![Manara Project AWS Solution Architecture](./solution%20architecture%20diagram.jpeg)

The diagram illustrates the complete AWS architecture, including the CI/CD pipeline, container deployment, networking, database connectivity, logging, secrets management, and IAM permissions.


### High-Level Architecture

``` text
Developer
   │
   ▼
GitHub Repository
   │
   ▼
AWS CodePipeline
   │
   ▼
AWS CodeBuild
   │
   ├── Build Docker image
   ├── Authenticate with Amazon ECR
   └── Push image to ECR
           │
           ▼
      Amazon ECR
           │
           ▼
      Amazon ECS Fargate
           │
           ▼
Application Load Balancer
           │
           ▼
      FastAPI API
           │
     ┌─────┼───────────────┬────────────────┐
     ▼     ▼               ▼                ▼
   RDS  CloudWatch         S3         Secrets Manager
PostgreSQL  Logs       Log Storage    DB Credentials
```

### Network Layout

The AWS environment is organized inside an Amazon VPC:

-   **Public subnets**
    -   Application Load Balancer
    -   ECS Fargate service for the training deployment design
-   **Private subnets**
    -   Amazon RDS PostgreSQL database
-   **VPC Endpoint**
    -   S3 Gateway VPC Endpoint to allow private S3 access without
        requiring a NAT Gateway

> The ECS service may use public IP addressing in the training
> configuration to reduce infrastructure complexity and avoid NAT
> Gateway costs. For a production deployment, ECS tasks should generally
> run in private subnets with appropriate VPC endpoints and/or
> controlled outbound connectivity.

------------------------------------------------------------------------

## AWS Services and Why They Are Used

### 1. GitHub

**Purpose:** Source code management and version control.

GitHub stores the application source code, Docker configuration,
CloudFormation templates, and CI/CD configuration.

**Why GitHub?**

-   Provides Git-based version control.
-   Supports collaboration and code review.
-   Acts as the source provider for AWS CodePipeline.
-   Keeps application and infrastructure code in one repository.

------------------------------------------------------------------------

### 2. AWS CodePipeline

**Purpose:** Automates the CI/CD workflow.

CodePipeline coordinates the deployment stages after a code change is
pushed to GitHub.

**Why CodePipeline?**

-   Connects source, build, and deployment stages.
-   Reduces manual deployment steps.
-   Provides a visible pipeline execution history.
-   Integrates directly with CodeBuild, ECR, and ECS.
-   Helps ensure that every approved code change follows the same
    process.

------------------------------------------------------------------------

### 3. AWS CodeBuild

**Purpose:** Builds the Docker image and prepares deployment artifacts.

CodeBuild executes the commands defined in `buildspec.yml`.

Typical operations include:

1.  Authenticate with Amazon ECR.
2.  Build the Docker image.
3.  Tag the image using the commit identifier.
4.  Push the image to ECR.
5.  Generate `imagedefinitions.json` for ECS deployment.

**Why CodeBuild?**

-   Fully managed build service.
-   No build server needs to be maintained.
-   Integrates with IAM, ECR, CloudWatch, and CodePipeline.
-   Supports repeatable and automated builds.

------------------------------------------------------------------------

### 4. Amazon ECR

**Purpose:** Stores Docker images for the application.

ECR contains the container images built by CodeBuild. ECS retrieves the
required image from ECR during deployment.

**Why ECR?**

-   Native integration with ECS.
-   Secure, private container image storage.
-   Supports image tagging and lifecycle policies.
-   Eliminates the need to operate a separate container registry.

------------------------------------------------------------------------

### 5. Amazon ECS with AWS Fargate

**Purpose:** Runs the FastAPI application container.

ECS manages the service and task lifecycle, while Fargate provides
serverless compute for running containers.

**Why ECS Fargate?**

-   No EC2 instances to provision or patch.
-   AWS manages the underlying container infrastructure.
-   Supports service deployments and task replacement.
-   Integrates with ALB, IAM, CloudWatch Logs, and ECR.
-   Suitable for running containerized APIs.

------------------------------------------------------------------------

### 6. Application Load Balancer

**Purpose:** Receives client HTTP requests and forwards them to the ECS
service.

The ALB exposes the application through a stable entry point and
performs health checks against the FastAPI container.

**Why ALB?**

-   Provides a single access point for users.
-   Distributes traffic to healthy ECS tasks.
-   Supports target-group health checks.
-   Makes it easier to add multiple application tasks later.
-   Separates public traffic handling from the application container.

------------------------------------------------------------------------

### 7. Amazon RDS for PostgreSQL

**Purpose:** Provides persistent relational database storage.

The FastAPI application uses PostgreSQL to store task data instead of
relying on in-memory Python lists.

**Why RDS PostgreSQL?**

-   Managed database service.
-   AWS handles common operational tasks such as backups and
    infrastructure maintenance.
-   PostgreSQL is a mature relational database.
-   Supports structured data, transactions, and SQL queries.
-   Keeps application data available beyond the lifecycle of an ECS
    task.

The database is placed in private subnets and is not intended to be
publicly accessible.

------------------------------------------------------------------------

### 8. Amazon CloudWatch Logs

**Purpose:** Collects and centralizes container and application logs.

ECS sends container stdout and stderr output to CloudWatch Logs using
the `awslogs` log driver.

**Why CloudWatch Logs?**

-   Centralized logging for ECS tasks.
-   Useful for troubleshooting deployment and runtime problems.
-   Supports log streams for individual containers.
-   Integrates with AWS monitoring and alerting capabilities.
-   Removes the need to log only to the container's local filesystem.

------------------------------------------------------------------------

### 9. Amazon S3

**Purpose:** Stores application log files and archived log data.

The application can upload buffered log content to an S3 bucket for
longer-term storage or later analysis.

**Why S3?**

-   Durable object storage.
-   Suitable for log archives and exported files.
-   Scales without managing storage servers.
-   Supports lifecycle rules for retention and cost control.
-   Can be accessed privately through an S3 Gateway VPC Endpoint.

CloudWatch is used for operational log visibility, while S3 is used for
file-based log storage.

------------------------------------------------------------------------

### 10. AWS Secrets Manager

**Purpose:** Stores and provides sensitive database credentials.

Database passwords should not be hard-coded in the source code, Docker
image, or GitHub repository.

**Why Secrets Manager?**

-   Separates secrets from application code.
-   Allows ECS tasks to retrieve secrets at runtime.
-   Supports controlled access through IAM.
-   Reduces the risk of exposing credentials in source control.
-   Supports secret rotation workflows.

------------------------------------------------------------------------

### 11. AWS IAM

**Purpose:** Controls access between AWS services and resources.

IAM roles are used for services such as:

-   CodePipeline
-   CodeBuild
-   ECS task execution
-   ECS application tasks

**Why IAM?**

-   Enforces authentication and authorization.
-   Allows permissions to be assigned to AWS services.
-   Supports least-privilege access.
-   Avoids storing long-term AWS access keys inside containers or source
    code.

------------------------------------------------------------------------

### 12. Amazon VPC

**Purpose:** Provides an isolated virtual network for the application
infrastructure.

The VPC contains the subnets, route tables, security groups, and
endpoints used by the application.

**Why VPC?**

-   Controls network boundaries.
-   Separates public-facing resources from the database.
-   Enables security-group-based traffic filtering.
-   Provides a foundation for private communication between AWS
    resources.

------------------------------------------------------------------------

### 13. Security Groups

**Purpose:** Control inbound and outbound network traffic.

The design uses separate security groups for the ALB, ECS tasks, and RDS
database.

Expected traffic rules:

  ------------------------------------------------------------------------
  Source           Destination                       Port Purpose
  ---------------- ---------------- --------------------- ----------------
  Internet users   ALB                                 80 Public HTTP
                                                          requests

  ALB security     ECS security                      8000 Forward API
  group            group                                  traffic

  ECS security     RDS security                      5432 PostgreSQL
  group            group                                  connection
  ------------------------------------------------------------------------

The database security group should not allow PostgreSQL access from the
entire internet.

------------------------------------------------------------------------

### 14. AWS CloudFormation

**Purpose:** Defines and provisions infrastructure as code.

The infrastructure is divided into CloudFormation templates so that
networking, storage/database resources, ECS resources, and CI/CD
resources can be managed separately.

**Why CloudFormation?**

-   Makes infrastructure repeatable.
-   Keeps infrastructure configuration in Git.
-   Reduces manual configuration errors.
-   Supports stack outputs and cross-stack references.
-   Makes updates and cleanup easier to manage.

------------------------------------------------------------------------

---

## Screenshots

The following screenshots document the deployed AWS resources and the running application. Store all images inside the `screenshots/` directory using the filenames below.

> Add screenshots as the deployment progresses. The README references are prepared in advance so the documentation can be completed consistently.

### 1. GitHub Repository

![GitHub Repository](./screenshots/01-github-repository.png)

Shows the repository structure, source code, infrastructure templates, and CI/CD configuration.

### 2. AWS CodePipeline

![AWS CodePipeline](./screenshots/02-codepipeline-success.png)

Shows a successful pipeline execution from source retrieval through build and deployment.

### 3. AWS CodeBuild

![AWS CodeBuild](./screenshots/03-codebuild-success.png)

Shows a successful build, including Docker image creation and pushing the image to Amazon ECR.

### 4. Amazon ECR

![Amazon ECR](./screenshots/04-ecr-images.png)

Shows the ECR repository and the Docker image tags generated by the pipeline.

### 5. Amazon ECS Cluster and Service

![Amazon ECS Service](./screenshots/05-ecs-service-running.png)

Shows the ECS cluster, running service, desired task count, and deployment status.

### 6. ECS Task Definition

![ECS Task Definition](./screenshots/06-ecs-task-definition.png)

Shows the task definition configuration, including CPU, memory, container port, IAM roles, and logging configuration.

### 7. Application Load Balancer

![Application Load Balancer](./screenshots/07-alb-target-group-healthy.png)

Shows the Application Load Balancer, listener configuration, target group, and healthy ECS target.

### 8. Running FastAPI Application

![Running FastAPI Application](./screenshots/08-fastapi-running.png)

Shows the application running through the Application Load Balancer DNS name.

### 9. FastAPI Swagger Documentation

![FastAPI Swagger Documentation](./screenshots/09-fastapi-swagger.png)

Shows the interactive FastAPI Swagger UI and the available API endpoints.

### 10. API Request and Response

![API Request and Response](./screenshots/10-api-request-response.png)

Shows an example request and response, such as creating a task or retrieving the task list.

### 11. Amazon RDS

![Amazon RDS](./screenshots/11-rds-instance-available.png)

Shows the RDS PostgreSQL instance, its availability status, and the relevant connectivity configuration.

### 12. RDS Connectivity Test

![RDS Connectivity Test](./screenshots/12-database-health-check.png)

Shows a successful database health check through the API endpoint.

### 13. Amazon CloudWatch Logs

![Amazon CloudWatch Logs](./screenshots/13-cloudwatch-logs.png)

Shows application and container logs received by CloudWatch Logs.

### 14. Amazon S3 Log Bucket

![Amazon S3 Log Bucket](./screenshots/14-s3-log-bucket.png)

Shows the S3 bucket and the uploaded application log files.

### 15. AWS Secrets Manager

![AWS Secrets Manager](./screenshots/15-secrets-manager.png)

Shows the database secret configuration without exposing the secret value.

### 16. VPC and Subnets

![VPC and Subnets](./screenshots/16-vpc-subnets.png)

Shows the VPC, public subnets, private subnets, and Availability Zone distribution.

### 17. Security Groups

![Security Groups](./screenshots/17-security-groups.png)

Shows the security-group rules for the ALB, ECS service, and RDS database.

### 18. CloudFormation Stacks

![CloudFormation Stacks](./screenshots/18-cloudformation-stacks.png)

Shows the successfully deployed CloudFormation stacks and their statuses.

### 19. IAM Roles

![IAM Roles](./screenshots/19-iam-roles.png)

Shows the IAM roles used by CodePipeline, CodeBuild, ECS task execution, and the ECS application task.

### 20. End-to-End Deployment Result

![End-to-End Deployment Result](./screenshots/20-end-to-end-result.png)

Shows the final successful state of the project: a running FastAPI application deployed through the AWS CI/CD pipeline and connected to RDS.


## Application Features

The FastAPI application provides task-management endpoints such as:

-   Health check
-   Database health check
-   List tasks
-   Create a task
-   Mark a task as completed

The application is designed to demonstrate API deployment rather than
provide a complete production task-management platform.

------------------------------------------------------------------------

## Repository Structure

``` text
manara-project/
├── app/
│   ├── main.py
│   ├── db.py
│   ├── s3_logger.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── infra/
│   ├── 01-network.yaml
│   ├── 02-storage-db.yaml
│   ├── 03-ecr-ecs-alb.yaml
│   └── 04-pipeline.yaml
│
├── scripts/
│   └── deploy.sh
│
├── buildspec.yml
├── .gitignore
└── README.md
```

### Directory Responsibilities

  -----------------------------------------------------------------------
  Directory/File                      Responsibility
  ----------------------------------- -----------------------------------
  `app/`                              FastAPI application and Docker
                                      configuration

  `main.py`                           API routes and application entry
                                      point

  `db.py`                             Database connection and persistence
                                      logic

  `s3_logger.py`                      Application log handling and S3
                                      integration

  `requirements.txt`                  Python dependencies

  `Dockerfile`                        Builds the application container
                                      image

  `infra/`                            AWS CloudFormation templates

  `scripts/`                          Deployment helper scripts

  `buildspec.yml`                     CodeBuild build and
                                      image-publishing instructions

  `.gitignore`                        Prevents unnecessary or sensitive
                                      files from being committed
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## CI/CD Workflow

When a developer pushes a change to the `main` branch:

1.  **GitHub** stores the new commit.
2.  **CodePipeline** detects the change.
3.  **CodeBuild** starts the build process.
4.  CodeBuild builds the Docker image from `app/Dockerfile`.
5.  CodeBuild authenticates with **Amazon ECR**.
6.  The image is tagged and pushed to ECR.
7.  CodeBuild generates `imagedefinitions.json`.
8.  CodePipeline deploys the new image to **ECS Fargate**.
9.  ECS starts a new task revision.
10. The ALB checks the application health endpoint.
11. Traffic is sent to healthy ECS tasks.

A commit-based image tag is preferred over relying only on the `latest`
tag because it provides better traceability between a running deployment
and its source code.

------------------------------------------------------------------------

## Networking and Security

The project follows a basic layered network design:

``` text
Internet
   │
   ▼
Application Load Balancer
   │
   ▼
ECS Fargate
   │
   ▼
Private RDS PostgreSQL
```

### Security Principles

-   RDS is not publicly accessible.
-   ECS accepts application traffic from the ALB security group.
-   RDS accepts database traffic from the ECS security group.
-   Database credentials are stored in Secrets Manager.
-   AWS service permissions are provided through IAM roles.
-   The source repository must not contain passwords, access keys, or
    other secrets.
-   Security groups should allow only the required ports and sources.

------------------------------------------------------------------------

## Infrastructure as Code

The CloudFormation templates are organized by responsibility.

### `01-network.yaml`

Creates foundational networking resources, such as:

-   VPC
-   Public and private subnets
-   Internet Gateway
-   Route tables
-   S3 Gateway VPC Endpoint
-   Security groups

### `02-storage-db.yaml`

Creates data and storage resources, such as:

-   S3 bucket for application logs
-   RDS subnet group
-   RDS PostgreSQL instance
-   Database secret
-   CloudFormation exports

### `03-ecr-ecs-alb.yaml`

Creates application hosting resources, such as:

-   ECR repository
-   ECS cluster
-   IAM roles
-   CloudWatch log group
-   ECS task definition
-   Application Load Balancer
-   Target group
-   Listener
-   ECS service

### `04-pipeline.yaml`

Creates CI/CD resources, such as:

-   Artifact S3 bucket
-   CodeBuild project
-   CodeBuild IAM role
-   CodePipeline
-   CodePipeline IAM role
-   GitHub CodeConnections integration

------------------------------------------------------------------------

## Configuration

The application requires configuration values for database connectivity
and logging.

Typical configuration values include:

``` text
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
S3_LOG_BUCKET
AWS_REGION
```

Sensitive values, especially `DB_PASSWORD`, should be supplied through
AWS Secrets Manager or ECS secret injection rather than committed to
GitHub.

The exact environment-variable names must match the names expected by
the application code and ECS task definition.

------------------------------------------------------------------------

## Deployment Overview

The deployment should be performed in dependency order:

1.  Create the networking stack.
2.  Create the storage and database stack.
3.  Create the ECR repository and application infrastructure.
4.  Build and push the initial Docker image.
5.  Configure and deploy the CI/CD pipeline.
6.  Trigger a pipeline execution.
7.  Verify the ECS service and ALB health.
8.  Test the API endpoints.
9.  Review CloudWatch Logs and RDS connectivity.

> Before deploying to a live AWS account, review all CloudFormation
> parameters, IAM permissions, security-group rules, database settings,
> and expected costs.

------------------------------------------------------------------------

## API Endpoints

The application exposes endpoints similar to the following:

  Method   Endpoint                  Description
  -------- ------------------------- -------------------------------------
  `GET`    `/`                       Returns a basic application message
  `GET`    `/health`                 Checks application health
  `GET`    `/health/db`              Checks database connectivity
  `GET`    `/tasks`                  Returns the available tasks
  `POST`   `/tasks`                  Creates a new task
  `PUT`    `/tasks/{task_id}/done`   Marks a task as completed

### Example: Create a Task

``` bash
curl -X POST "http://<ALB-DNS-NAME>/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title":"Complete AWS deployment"}'
```

### Example: Retrieve Tasks

``` bash
curl "http://<ALB-DNS-NAME>/tasks"
```

Replace `<ALB-DNS-NAME>` with the DNS name of the deployed Application
Load Balancer.

------------------------------------------------------------------------

## Observability and Logging

The project uses two logging paths:

### CloudWatch Logs

Used for:

-   Real-time troubleshooting
-   ECS container logs
-   Application errors
-   Deployment investigation
-   Operational visibility

### Amazon S3

Used for:

-   Application log-file storage
-   Exported or archived log content
-   Longer-term object-based retention

The S3 logging implementation is intended for learning and
demonstration. A production system should consider a managed
log-delivery architecture, buffering strategy, encryption, lifecycle
policies, and failure handling.

------------------------------------------------------------------------

## Cost Considerations

The project is designed with cost awareness in mind.

Potential cost-generating resources include:

-   Application Load Balancer
-   Amazon RDS
-   ECS Fargate task runtime
-   CodeBuild build minutes
-   S3 storage and requests
-   CloudWatch Logs ingestion and retention
-   ECR image storage

Cost-control decisions may include:

-   Using small training-sized resources.
-   Avoiding a NAT Gateway in the training design.
-   Using an S3 Gateway VPC Endpoint.
-   Applying ECR image lifecycle policies.
-   Configuring CloudWatch log retention.
-   Stopping or deleting resources when the project is not in use.

AWS pricing and service availability vary by region and configuration.
Review the current AWS pricing pages before deployment.

------------------------------------------------------------------------

## Security Considerations

This project is educational and should be hardened before production
use.

Recommended improvements include:

-   Use HTTPS with an ACM certificate.
-   Redirect HTTP traffic to HTTPS.
-   Run ECS tasks in private subnets.
-   Use VPC endpoints where appropriate.
-   Apply least-privilege IAM policies.
-   Encrypt RDS and S3 data.
-   Enable database backups and deletion protection when appropriate.
-   Store secrets only in Secrets Manager.
-   Configure CloudWatch log retention.
-   Add monitoring and alerting.
-   Avoid exposing administrative endpoints publicly.
-   Add authentication and authorization to the API.
-   Use image scanning and dependency vulnerability checks.

------------------------------------------------------------------------

## Limitations and Future Improvements

Possible future improvements include:

-   HTTPS support through AWS Certificate Manager.
-   Private ECS subnets with controlled outbound connectivity.
-   ECS service auto scaling.
-   Multi-AZ production database configuration.
-   RDS Proxy for connection management.
-   API authentication using Amazon Cognito or another identity
    provider.
-   Automated tests in CodeBuild.
-   Static analysis and security scanning.
-   Blue/green or canary deployments.
-   CloudWatch alarms and notifications.
-   Centralized managed log delivery to S3.
-   Database migration management using Alembic.
-   API documentation and integration tests.
-   WAF protection for internet-facing workloads where required.

------------------------------------------------------------------------

## Cleanup

To avoid unnecessary AWS charges, delete resources when the project is
no longer needed.

Cleanup should be performed carefully and in dependency order:

1.  Disable or remove the CI/CD pipeline.
2.  Delete the ECS service and related application resources.
3.  Delete the ECR repository after reviewing stored images.
4.  Delete the RDS stack after confirming that required data is backed
    up.
5.  Empty the S3 buckets if CloudFormation requires it.
6.  Delete the storage/database stack.
7.  Delete the networking stack.

**Important:** RDS and S3 may contain data that cannot be recovered
after deletion. Always verify backups and retention requirements before
cleanup.

------------------------------------------------------------------------

## Learning Outcomes

By completing this project, the developer practices:

-   Designing a cloud architecture on AWS.
-   Building a REST API with FastAPI.
-   Creating Docker images.
-   Using Amazon ECR as a container registry.
-   Deploying containers with ECS Fargate.
-   Configuring an Application Load Balancer.
-   Connecting an application to RDS PostgreSQL.
-   Designing VPC subnets and security groups.
-   Managing secrets with AWS Secrets Manager.
-   Using IAM roles for AWS service access.
-   Implementing AWS-native CI/CD with CodePipeline and CodeBuild.
-   Managing infrastructure through CloudFormation.
-   Collecting and storing application logs.
-   Considering security, reliability, and cloud costs.

------------------------------------------------------------------------

## License

This project is intended for educational and portfolio purposes. Add an
appropriate license here if the repository will be distributed or reused
publicly.

------------------------------------------------------------------------

## Author

**Anas**

GitHub: [Dev-Anas-10](https://github.com/Dev-Anas-10)

Repository:
[manara-project](https://github.com/Dev-Anas-10/manara-project)
