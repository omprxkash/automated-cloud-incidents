# automated-cloud-incidents

Research and tooling for automated cloud reliability — from incident triaging and troubleshooting guide generation to root cause analysis using knowledge graphs and LLMs.

---

## Projects

### TSGen — Automated Troubleshooting Guide Generation from Cloud Incidents
Generates structured troubleshooting guides automatically from raw incident reports. Extracts symptoms, affected components, and resolution steps, then templates them into runbooks that on-call engineers can follow without prior context on the incident.

### TRIANGLE — Automated Incident Triaging for Cloud Reliability Data

As cloud service systems grow in scale and complexity, incidents that indicate unplanned interruptions and outages become unavoidable. Rapid and accurate triage of these incidents to the appropriate responsible teams is crucial to maintain service reliability and prevent significant financial losses. However, existing incident triage methods relying on manual operations and predefined rules often struggle with efficiency and accuracy due to the heterogeneity of incident data and the dynamic nature of domain knowledge across multiple teams.

To solve these issues, we propose TRIANGLE, an end-to-end incident triage system based on a multi-agent framework. TRIANGLE leverages a **semantic distillation mechanism** to tackle the issue of semantic heterogeneity in incident data, enhancing the accuracy of incident triage. Additionally, we introduce **multi-role agents** and a **negotiation mechanism** to emulate human engineers' workflows, effectively handling decentralized and dynamic domain knowledge from multiple teams. Furthermore, our system incorporates an **automated troubleshooting information collection and mitigation mechanism**, reducing the reliance on human labor and enabling fully automated end-to-end incident triage.

Extensive experiments conducted on a real-world cloud production environment demonstrate that TRIANGLE significantly improved incident triage accuracy (up to **97%**) and reduced Time to Engage (TTE) by as much as **91%**, demonstrating substantial operational impact across diverse cloud services.

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
