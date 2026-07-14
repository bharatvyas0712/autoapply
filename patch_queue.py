import os

file_path = os.path.join('backend', 'controllers', 'applicationsController.js')
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

queue_code = """
class AsyncQueue {
  constructor() {
    this.queue = [];
    this.isProcessing = false;
  }
  async add(task) {
    return new Promise((resolve, reject) => {
      this.queue.push({ task, resolve, reject });
      if (!this.isProcessing) this.process();
    });
  }
  async process() {
    this.isProcessing = true;
    while (this.queue.length > 0) {
      const { task, resolve, reject } = this.queue.shift();
      try {
        const result = await task();
        resolve(result);
      } catch (err) {
        reject(err);
      }
    }
    this.isProcessing = false;
  }
}
const autoSubmitQueue = new AsyncQueue();
"""

# Insert Queue at the top after requires
if "class AsyncQueue" not in content:
    lines = content.split('\\n')
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('// GET /api/applications'):
            insert_idx = i
            break
    
    lines.insert(insert_idx, queue_code)
    content = '\\n'.join(lines)

# Now find autoSubmitApplication and wrap the axios call
target_start = """    // Trigger automation service async
    const resumePath = formData.resume_url ? path.join(__dirname, '..', formData.resume_url) : null;
    try {
      const response = await axios.post("""

replacement = """    // Trigger automation service async
    const resumePath = formData.resume_url ? path.join(__dirname, '..', formData.resume_url) : null;
    
    autoSubmitQueue.add(async () => {
      try {
        const response = await axios.post("""

if target_start in content:
    content = content.replace(target_start, replacement)
    
    # We also need to close the queue block.
    # The try-catch block for axios is:
    #     } catch (automErr) {
    #       ...
    #       );
    #     }
    #   } catch (err) {
    # We replace:
    
    catch_block = """      await db.query(
        'UPDATE automation_sessions SET completed_at = NOW(), error_message = ? WHERE id = ?',
        [automErr.message, sessionId]
      );
    }
  } catch (err) {"""

    catch_replacement = """      await db.query(
        'UPDATE automation_sessions SET completed_at = NOW(), error_message = ? WHERE id = ?',
        [automErr.message, sessionId]
      );
    }
  }); // End of autoSubmitQueue.add
  } catch (err) {"""
    
    content = content.replace(catch_block, catch_replacement)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched!")
