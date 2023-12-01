import openai
import json
import time

# Initialize the OpenAI client
api_key = 'your-api-key'
client = openai.Client(api_key='<OPEN AI API KEY>')
assistants = {}  # Dictionary to store assistants

def create_new_assistant():
    # Prompt for assistant details
    name = input("Enter a name for the new assistant: ")
    instructions = input("Enter instructions for the assistant: ")
    model = input("Enter the model to use (e.g., 'gpt-3.5-turbo-1106'): ")

    # Determine which tools to enable
    tools = []
    if input("Enable Code Interpreter tool? (yes/no): ").lower() == 'yes':
        tools.append({"type": "code_interpreter"})
    
    if input("Enable Retrieval tool? (yes/no): ").lower() == 'yes':
        tools.append({"type": "retrieval"})

    # Add custom functions
    add_functions = input("Do you want to add custom functions? (yes/no): ").lower()
    while add_functions == 'yes':
        function_name = input("Enter the function name: ")
        function_description = input("Enter the function description: ")
        parameter_name = input("Enter the parameter name: ")
        parameter_description = input("Enter the parameter description: ")
        parameter_type = input("Enter the parameter type (e.g., 'string', 'number', 'boolean'): ")

        # Construct the parameter schema based on user inputs
        parameter_schema = {
            "type": "object",
            "properties": {
                parameter_name: {
                    "type": parameter_type,
                    "description": parameter_description
                }
            },
            "required": [parameter_name]
        }

        try:
            # Add the custom function to the tools list with the constructed schema
            tools.append({
                "type": "function",
                "function": {
                    "name": function_name,
                    "description": function_description,
                    "parameters": parameter_schema
                }
            })
            print("Function added successfully.")
        except json.JSONDecodeError:
            print("Error: Invalid JSON format for parameters.")

        add_functions = input("Do you want to add another function? (yes/no): ").lower()


    # Create the new assistant
    assistant = client.beta.assistants.create(
        name=name,
        instructions=instructions,
        tools=tools,
        model=model
    )

    # Store the assistant in the dictionary
    assistants[assistant.id] = assistant
    print(f"Assistant created with ID: {assistant.id}")


def choose_assistant():
    
    assistant_id = input("Enter the Assistant ID: ")
    return assistant_id





def chat_with_assistant(assistant_id):
    thread = client.beta.threads.create()

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # Check the status of the last run before adding a new message
        runs = client.beta.threads.runs.list(thread_id=thread.id)
        if runs.data:
            last_run_status = runs.data[0].status
            while last_run_status not in ['completed', 'failed', 'cancelled', 'expired']:
                print("Waiting for the current run to complete...")
                time.sleep(1)
                last_run_status = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=runs.data[0].id
                ).status

        # Create a message with the user input
        client.beta.threads.messages.create(
            role="user",
            content=user_input,
            thread_id=thread.id
        )

        # Create a run with the assistant and the thread
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        # Polling for run completion
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            ).status

            if run_status in ['completed', 'failed', 'cancelled', 'expired']:
                break
            elif run_status == 'requires_action':
                print('Invoking custom function...')
                                        # Get the run details
                run_details = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )

                tool_calls = run_details.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []

                for call in tool_calls:
                    tool_call_id = call.id
                    function_name = call.function.name

                    if function_name == "TheSumOfLife":
                        # Extract the arguments from the function call
                        arguments = json.loads(call.function.arguments) 

                        # Perform your custom logic here. For demonstration, let's just divide 42 by thePowerOf
                        the_power_of = int(arguments['humanYears'])
                        custom_output = str(42 * the_power_of) if the_power_of != 0 else "Error: Division by zero"

                        tool_outputs.append({
                            "tool_call_id": tool_call_id,
                            "output": custom_output
                        })

                # Submit the tool outputs if any
                if tool_outputs:
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                    print(f'Custom data submitted: {custom_output}')
                else:
                    print('No tool outputs to submit.')

            elif run_status in ['completed', 'failed', 'cancelled', 'expired']:
                    break
            else:
                time.sleep(1)



        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )

        for message in messages.data:
            if message.role == 'assistant':
                print(f"Assistant: {message.content[0].text.value}")


def list_assistants():
    print("\nListing Available Assistants...")
    try:
        my_assistants = client.beta.assistants.list(order="desc", limit="20")
        for assistant in my_assistants.data:
            print(f"ID: {assistant.id}, Name: {assistant.name}")
    except Exception as e:
        print(f"An error occurred: {e}")

def delete_assistant():
    list_assistants()  # Show the list of assistants for easier selection

    assistant_id = input("Enter the ID of the assistant to delete: ")
    confirmation = input(f"Are you sure you want to delete the assistant with ID {assistant_id}? (yes/no): ")

    if confirmation.lower() == 'yes':
        try:
            client.beta.assistants.delete(assistant_id)
            print(f"Assistant with ID {assistant_id} has been deleted.")
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("Assistant deletion cancelled.")

def main_menu():
    global assistant_id  # Declare assistant_id as a global variable




    while True:
    
       # Wait for space bar press
        print("Press Space bar and Enter to show options...")
        if input() != ' ':
            continue

        print("\nOpenAI Assistant Manager")
        print("--------------------------")
        print("1. Create New Assistant")
        print("2. Choose Existing Assistant")
        print("3. Chat with Assistant")
        print("4. List Assistants")
        print("5. Delete an Assistant")
        print("6. Exit")
        print("--------------------------")
        choice = input("Enter your choice: ")

        if choice == "1":
            create_new_assistant()
        elif choice == "2":
            assistant_id = choose_assistant()
        elif choice == "3":
            if assistant_id:
                chat_with_assistant(assistant_id)
            else:
                print("No assistant selected. Please choose an assistant first.")
        elif choice == "4":
            list_assistants()
        elif choice == "5":
            delete_assistant()
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    assistant_id = 'ASSISTANT ID'  # To keep track of the currently selected assistant
    main_menu()

