# automated-cloud-incidents

Research and tooling for automated cloud reliability — from incident triaging and troubleshooting guide generation to root cause analysis using knowledge graphs and LLMs.

---

## Projects

### TSGen — Automated Troubleshooting Guide Generation from Cloud Incidents
Generates structured troubleshooting guides automatically from raw incident reports. Extracts symptoms, affected components, and resolution steps, then templates them into runbooks that on-call engineers can follow without prior context on the incident.

### TRIANGLE — Automated Incident Triaging for Cloud Reliability Data
Triage pipeline for incoming cloud incidents. Classifies severity, routes to the right team, and surfaces similar past incidents from a historical index — reducing the time from alert to the right person by automating the first few steps of on-call response.

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
Python · PyTorch · LangChain · NetworkX · Neo4j · OpenStack SDK · Terraform
