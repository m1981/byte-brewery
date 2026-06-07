LLM Usage Guide for py-diagram                                                                                        
                                                                                                                       
 ### The Core Problem                                                                                                  
                                                                                                                       
 When an LLM works on a Python codebase, it faces a context budget problem. It can read files one at a time, but it    
 never gets a structural overview — which classes exist, how they relate, what depends on what. It's like navigating a 
 city by entering one building at a time without ever seeing the map.                                                  
                                                                                                                       
 py-diagram generates that map in a token-efficient format.                                                            
                                                                                                                       
 ### Decision Tree                                                                                                     
                                                                                                                       
 ```                                                                                                                   
   Need to understand the codebase structure?                                                                          
   │                                                                                                                   
   ├─ "What types/classes exist and how do they relate?"                                                               
   │   → py-diagram src/ --format token                                                                                
   │                                                                                                                   
   ├─ "What does this specific module export?"                                                                         
   │   → py-diagram --source src/module.py --format token                                                              
   │                                                                                                                   
   ├─ "I need a bounded overview (large codebase)"                                                                     
   │   → py-diagram src/ --format token --max-classes 40                                                               
   │                                                                                                                   
   ├─ "I need to see private/dunder members too"                                                                       
   │   → py-diagram src/ --format token --include-private --include-dunder                                             
   │                                                                                                                   
   ├─ "Generating docs for humans"                                                                                     
   │   → py-diagram src/ --format mermaid --output docs/classes.md                                                     
   │                                                                                                                   
   └─ "I just need one subsystem"                                                                                      
       → py-diagram src/agent --format token                                                                           
 ```                                                                                                                   
                                                                                                                       
 ### The Token Format Is the LLM Format                                                                                
                                                                                                                       
 The --format token output was designed specifically for LLM consumption. Here's why it works:                         
                                                                                                                       
 ```                                                                                                                   
   [MODULE] agent.tool_executor        ← grouping by module (not class)                                                
     [IMPORT] from src.protocols import ToolRegistryProtocol  ← dependencies                                           
     [CLASS] ToolCall(module=agent.tool_executor) @dataclass [line 42]                                                 
       FIELDS: id:str, name:str, arguments:dict                                                                        
     [CLASS] ToolExecutor(module=agent.tool_executor) [line 67]                                                        
       METHODS: execute_all(tool_calls:list[ToolCall])->list[ToolResult] [line 99]                                     
     [FUNCTIONS]                                                                                                       
       helper_fn(x:int)->str [line 105]                                                                                
   [RELATIONSHIPS]                                                                                                     
     ToolExecutor --uses--> ToolCall                                                                                   
 ```                                                                                                                   
                                                                                                                       
 Why this is better than reading source files:                                                                         
```                                                                                                
 ┌─────────────────────────────────────────┬─────────────────────────────────┐                                         
 │ Source file reading                     │ Token format                    │                                         
 ├─────────────────────────────────────────┼─────────────────────────────────┤                                         
 │ 1 file = ~200-500 lines                 │ All files = ~40KB               │                                         
 ├─────────────────────────────────────────┼─────────────────────────────────┤                                         
 │ Sees implementation details             │ Sees structural contracts       │                                         
 ├─────────────────────────────────────────┼─────────────────────────────────┤                                         
 │ Must read N files to find a class       │ All classes in one output       │                                         
 ├─────────────────────────────────────────┼─────────────────────────────────┤                                         
 │ Relationships are implicit (in imports) │ Relationships are explicit      │                                         
 ├─────────────────────────────────────────┼─────────────────────────────────┤                                         
 │ No line numbers                         │ [line 42] — jump straight there │                                         
 └─────────────────────────────────────────┴─────────────────────────────────┘                                         
```                                                                                      
 ### Practical Patterns                                                                                                
                                                                                                                       
 Pattern 1: Orientation — "I just arrived at this codebase"                                                            
                                                                                                                       
 ```bash                                                                                                               
   py-diagram src/ --format token --max-classes 50                                                                     
 ```                                                                                                                   
                                                                                                                       
 This gives a bounded structural overview. The LLM learns:                                                             
 - What modules exist                                                                                                  
 - What classes each module defines                                                                                    
 - What methods each class has (with types)                                                                            
 - What functions exist at module level                                                                                
 - What the imports are (dependency hints)                                                                             
 - How classes relate (inheritance, composition, uses)                                                                 
                                                                                                                       
 Pattern 2: Focused work — "I'm modifying the providers"                                                               
                                                                                                                       
 ```bash                                                                                                               
   py-diagram src/providers --format token                                                                             
 ```                                                                                                                   
                                                                                                                       
 Or for a single file:                                                                                                 
                                                                                                                       
 ```bash                                                                                                               
   py-diagram --source src/providers/gemini.py --format token                                                          
 ```                                                                                                                   
                                                                                                                       
 Pattern 3: Impact analysis — "I'm changing ToolCall, what uses it?"                                                   
                                                                                                                       
 Run the full token output and grep:                                                                                   
                                                                                                                       
 ```bash                                                                                                               
   py-diagram src/ --format token 2>/dev/null | grep -B2 "ToolCall"                                                    
 ```                                                                                                                   
                                                                                                                       
 The [RELATIONSHIPS] section at the bottom immediately shows:                                                          
                                                                                                                       
 ```                                                                                                                   
   ToolExecutor --uses--> ToolCall                                                                                     
   AnthropicProvider --uses--> ToolCall                                                                                
   NormalizedResponse --composes--> ToolCall                                                                           
 ```                                                                                                                   
                                                                                                                       
 Pattern 4: Before writing new code — "Where does this fit?"                                                           
                                                                                                                       
 Before creating a new class, check what exists:                                                                       
                                                                                                                       
 ```bash                                                                                                               
   py-diagram src/ --format token 2>/dev/null | grep "\[CLASS\]"                                                       
 ```                                                                                                                   
                                                                                                                       
 This prevents duplicate definitions and reveals naming conventions.                                                   
                                                                                                                       
 Pattern 5: Generating documentation                                                                                   
                                                                                                                       
 ```bash                                                                                                               
   py-diagram src/ --format mermaid --output docs/architecture.md                                                      
 ```                                                                                                                   
                                                                                                                       
 Mermaid renders natively in GitHub, Obsidian, and most Markdown viewers.                                              
                                                                                                                       
 ### What the LLM Should NOT Do                                                                                        
```
 ┌─────────────────────────────────────────────┬───────────────────────────────────────────────────────────────────┐   
 │ Anti-pattern                                │ Why it's wrong                                                    │   
 ├─────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤   
 │ Read every .py file to understand structure │ Use py-diagram first, then read only the files you need to modify │   
 ├─────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤   
 │ Use --format mermaid for context injection  │ Too verbose for LLM context. Use --format token                   │   
 ├─────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤   
 │ Skip the [RELATIONSHIPS] section            │ It's the most valuable part — shows dependency direction          │   
 ├─────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤   
 │ Use --include-dunder unless debugging       │ Dunder methods add noise. Default filtering is correct            │   
 ├─────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤   
 │ Run on the entire repo (including tests)    │ Use --skip tests or target src/ only                              │   
 └─────────────────────────────────────────────┴───────────────────────────────────────────────────────────────────┘   
```                                                                                                      
 ### Integration with Agent Workflows                                                                                  
                                                                                                                       
 The ideal LLM workflow:                                                                                               
                                                                                                                       
 ```                                                                                                                   
   1. py-diagram src/ --format token          → structural overview                                                    
   2. Read the specific file(s) to modify     → implementation detail                                                  
   3. py-diagram --source modified.py --format token  → verify changes                                                 
 ```                                                                                                                   
                                                                                                                       
 Step 1 replaces reading 10-20 files. Step 3 is optional but useful for verifying the change didn't break structural   
 expectations.                                                                                                         
                                                                                                                       
 ### Output Size Budget                                                                                                
                                                                                                                       
 For context window management:                                                                                        
```                                                                                                               
 ┌──────────────────────┬─────────────────────────────────────────────────┬───────────────┐                            
 │ Codebase size        │ Recommended command                             │ Output size   │                            
 ├──────────────────────┼─────────────────────────────────────────────────┼───────────────┤                            
 │ Small (<20 files)    │ py-diagram src/ --format token                  │ ~10-20 KB     │                            
 ├──────────────────────┼─────────────────────────────────────────────────┼───────────────┤                            
 │ Medium (20-60 files) │ py-diagram src/ --format token --max-classes 40 │ ~15-25 KB     │                            
 ├──────────────────────┼─────────────────────────────────────────────────┼───────────────┤                            
 │ Large (60+ files)    │ py-diagram src/subsystem --format token         │ target ~15 KB │                            
 ├──────────────────────┼─────────────────────────────────────────────────┼───────────────┤                            
 │ Single module        │ py-diagram --source file.py --format token      │ ~1-3 KB       │                            
 └──────────────────────┴─────────────────────────────────────────────────┴───────────────┘                            
```                                                                                                              
 The sweet spot is 15-25 KB of token output — enough to see the full structure without consuming too much context      
 budget.                                               