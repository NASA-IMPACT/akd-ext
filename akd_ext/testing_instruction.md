# Testing MCP Server with MCP Inspector

This document provides instructions for testing the FastMCP cloud-hosted MCP server locally using MCP Inspector.

Follow these steps to test the MCP server using MCP Inspector.



## Step 1: Install and Start MCP Inspector

Open your terminal/command prompt and run:
```bash
npx @modelcontextprotocol/inspector
```

This will:
- Download and install MCP Inspector (first time only)
- Start the inspector
- Automatically open it in your browser at `http://localhost:6274`

> **Note:** Keep the terminal window open while using the inspector.

---

## Step 2: Configure Connection Settings

In the MCP Inspector interface, you'll see a connection form. Configure it as follows:

### **Transport Type**
Select: `Streamable HTTP`

### **URL**
Enter your Fastmcp cloud url. 

### **Connection Type**
Select: `Via Proxy` (should be default)

### **Authentication**
1. Expand the **"Authentication"** section if it's collapsed
2. Under **"Custom Headers"**:
   - Make sure the toggle switch next to "Authorization" is **ON** (enabled)
   - Header name: `Authorization`
   - Header value: `Bearer YOUR_API_KEY_HERE`
   
   ⚠️ **Important:** Replace `YOUR_API_KEY_HERE` with the actual API key provided to you

**Example:**
If your API key is `fmcp_abc123xyz`, enter:
```
Bearer fmcp_abc123xyz
```

---

## Step 3: Connect to the Server

1. After entering all settings, click the **"Connect"** button
2. Wait a few seconds for the connection to establish
3. If successful, you should see the page change to show available tools

---

## Step 4: Test the Endpoints

Once connected:

### **View Available Tools**
- You should automatically see a list of tools on the left side
- Or click **"List Tools"** button if needed

### **Test Individual Tools**
1. Click on any tool name from the list
2. Fill in any required parameters
3. Click **"Run"** or **"Execute"** to test the tool
4. View the response/results

---