# automated-cloud-incidents

Research and tooling for automated cloud reliability — from incident triaging and troubleshooting guide generation to root cause analysis using knowledge graphs and LLMs.

---

## Projects

### TSGen — Automated Troubleshooting Guide Generation from Cloud Incidents
Generates structured troubleshooting guides automatically from raw incident reports. Extracts symptoms, affected components, and resolution steps, then templates them into runbooks that on-call engineers can follow without prior context on the incident.

### TRIANGLE — Automated Incident Triaging for Cloud Reliability Data

> *Build a multi-agent triage system to route cloud incidents to the right team.*

As cloud service systems grow in scale and complexity, incidents that indicate unplanned interruptions and outages become unavoidable. Rapid and accurate triage of these incidents to the appropriate responsible teams is crucial to maintain service reliability and prevent significant financial losses. However, existing incident triage methods relying on manual operations and predefined rules often struggle with efficiency and accuracy due to the heterogeneity of incident data and the dynamic nature of domain knowledge across multiple teams.

To solve these issues, TRIANGLE is an end-to-end incident triage system based on a multi-agent framework. It leverages a **semantic distillation mechanism** to tackle the issue of semantic heterogeneity in incident data, enhancing the accuracy of incident triage. Additionally, it introduces **multi-role agents** and a **negotiation mechanism** to emulate human expert collaboration — enabling the system to dynamically adapt to evolving domain knowledge and route incidents to the right team with high precision.

### KG Clustering + Graphlet Inference for Historical Cloud Incidents (RCA with LLMs)
Builds a knowledge graph over historical incident data, clusters incidents by failure mode using graphlet-based structural features, and uses an LLM to reason over the subgraph around a new incident for root cause analysis. Combines graph structure with language model reasoning rather than treating RCA as a pure retrieval problem.

---

## Also in this repo

### `openstack/`
Infrastructure provisioning and configuration tooling for OpenStack deployments — Terraform modules, Heat templates, and scripts for managing compute, networking, and storage resources.

### `stack-vm/`
A minimal stack-based virtual machine implemented from scratch. Covers bytecode design, an assembler, and the interpreter loop — useful for understanding how VMs work at the instruction level.

---

## Stack
Python · PyTorch · LangChain · LangGraph · NetworkX · Neo4j · OpenStack SDK · Terraform
