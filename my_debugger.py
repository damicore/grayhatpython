from ctypes import *
from my_debugger_defines import *

kernel32 = windll.kernel32

class debugger():

    def __init__(self):
        self.h_process = None
        self.pid = None
        self.debugger_active = False

    def load(self,path_to_exe):

        #dwCreation flag determines how to create the process
        #set creation_flags = CREATE_NEW_CONSOLE if you want
        #to see the calculator GUI
        creation_flags = DEBUG_PROCESS

        #instantiate the structs
        startupinfo = STARTUPINFO()
        process_information = PROCESS_INFORMATION()

        # The following two options allow the started process
        # to be shown as a separate window. This also illustrates
        # how different settings in the STARTUPINFO struct can affect
        # the debuggee.
        startupinfo.dwFlags = 0x1
        startupinfo.wShowWindow = 0x0

        #initializing of cb var in STARTUPINFO
        #it's the size of the struct itself

        startupinfo.cb = sizeof(startupinfo)

        if kernel32.CreateProcessA(path_to_exe,
                                    None,
                                    None,
                                    None,
                                    None,
                                    creation_flags,
                                    None,
                                    None,
                                    byref(startupinfo),
                                    byref(process_information)):

            print("[*] We have succesfully launched the process!")
            print("[*] PID: %d" % process_information.dwProcessId)

            # Obtain a valid handle to the newly created process
            # and store it for future access
            self.h_process = self.open_process(process_information.dwProcessId)

        else:
            print("[*] Error: 0x%08x." % kernel32.GetLastError())


    def open_process(self,pid):

        h_process = kernel32.OpenProcess(PROCESS_ALL_ACCESS,False,pid)
        return h_process

    def attach(self,pid):

        self.h_process = self.open_process(pid)

        # We attempt to attach to the process
        # if it fails we exit the Call

        if kernel32.DebugActiveProcess(pid):
            self.debugger_active = True
            self.pid = int(pid)
            #self.run()
        else:
            print("[*] Unable to attach to the process.")

    def run(self):
        # Now we have to poll the debugger for
        # debugging events

        while self.debugger_active == True:
            self.get_debug_event()

    def get_debug_event(self):

        debug_event = DEBUG_EVENT()
        continue_status = DBG_CONTINUE

        if kernel32.WaitForDebugEvent(byref(debug_event),INFINITE):

            # We aren't going to build any event handlers
            # just yet. Let's just resume the process for now.

            # raw_input("Press a key to continue...")
            # self.debugger_active = False
            kernel32.ContinueDebugEvent(\
                                        debug_event.dwProcessId,\
                                        debug_event.dwThreadId,\
                                        continue_status)

    def detach(self):

        if kernel32.DebugActiveProcessStop(self.pid):
            print("[*] Finished debugging. Exiting...")
            return True
        else:
            print("There was an error.")
            return False

    def open_thread (self, thread_id):

        h_thread = kernel32.OpenThread(THREAD_ALL_ACCESS, None, thread_id)

        if h_thread is not None:
            return h_thread
        else:
            print("[*] Could not obtain a valid thread handle.")
            return False

    def enumerate_threads(self):

        thread_entry = THREADENTRY32()
        thread_list = []
        snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, self.pid)
        print("snapshot = " + str(snapshot))

        if snapshot is not None:
            #You have to set the size of the struct
            #or the call will fail
            thread_entry.dwSize = sizeof(thread_entry)
            success = kernel32.Thread32First(snapshot, byref(thread_entry))
            print("sizeof(threadentry) = " + str(thread_entry.dwSize))
            print("self.pid = "  + str(self.pid) + " and thread_entry.th32OwnerProcessID = " + str(thread_entry.th32OwnerProcessID))
            print("ERROR: %s" % FormatError(kernel32.GetLastError()))

            while success:
                if thread_entry.th32OwnerProcessID == self.pid:
                    thread_list.append(thread_entry.th32ThreadID)
                    success = kernel32.Thread32Next(snapshot, byref(thread_entry))

            kernel32.CloseHandle(snapshot)
            return thread_list

        else:
            return False

    def get_thread_context (self, thread_id=None, h_thread=None):

        context = CONTEXT()
        context.ContextFlags = CONTEXT_FULL | CONTEXT_DEBUG_REGISTERS
