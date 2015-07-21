# Garbo -  Graph-based cloud resource cleanup

## Notes
* This is a *very* early version
 * Only AWS discovery
 * No resources cleanup, just reporting

## Quick Start
1. Copy and modify the example configuration file

  ```bash
  cp garbo.cfg.example garbo.cfg.example
  vim garbo.cfg
  ```
2. Create a Core Resources file, eg.

  ```yml
  --- # My applications
  Backend:
  - "AWS://AutoScalingGroup/us-east-1/Backend-ASG"
  QA:
  - "AWS://Instance/us-east-1/i-abc12345"  # Mock server
  ```
3. Find unused resources

  ```bash
  python garbo.py -d -g -a /path/to/core_resources.yml
  # And start a simple web server to view the resulted d3js graph (assuming Python 2.7)
  python -m SimpleHTTPServer 8000
  ```
4. Browse to: <http://localhost:8000/d3js/index.html>

## Usage
```
usage: garbo.py [-h] [--applications APPLICATIONS] [--discovery] [--gen-d3js]

optional arguments:
  -h, --help            show this help message and exit
  --applications APPLICATIONS, -a APPLICATIONS
                        YAML file containing Core Resources per application
  --discovery, -d       Perform a discovery (don't use stored graph).
                          default: False
  --gen-d3js, -g        Generate a json file for D3JS Directed Force Graph.
                          default: False
```