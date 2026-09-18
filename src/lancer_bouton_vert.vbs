Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\richa\JobHunter"
WshShell.Run """C:\Users\richa\AppData\Local\Programs\Python\Python314\pythonw.exe"" ""C:\Users\richa\JobHunter\floating_button.pyw""", 0, False
