using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Collections.Concurrent;
using UnityEngine;

public class CommandServer : MonoBehaviour
{
    TcpListener server;
    Thread serverThread;
    public int port = 8052;
    public DoorController door;
    public LightController lightCtrl;
    public BedController bed;
    public NurseController nurse;
    public PlayerMover mover;
    ConcurrentQueue<string> commandQueue = new ConcurrentQueue<string>();

    void Start()
    {
        serverThread = new Thread(StartServer);
        serverThread.IsBackground = true;
        serverThread.Start();
        Debug.Log("Command Server started on port " + port);
    }

    void StartServer()
    {
        server = new TcpListener(IPAddress.Any, port);
        server.Start();
        while (true)
        {
            TcpClient client = server.AcceptTcpClient();
            NetworkStream stream = client.GetStream();
            byte[] buffer = new byte[1024];
            int length = stream.Read(buffer, 0, buffer.Length);
            string cmd = Encoding.UTF8.GetString(buffer, 0, length).Trim();
            commandQueue.Enqueue(cmd);
            client.Close();
        }
    }

    void Update()
    {
        while (commandQueue.TryDequeue(out string cmd))
        {
            HandleCommand(cmd);
        }
    }

    void HandleCommand(string cmd)
    {
        // ===== ROOM ACTIONS =====
        if (cmd == "OPEN_DOOR") door.OpenDoor();
        else if (cmd == "CLOSE_DOOR") door.CloseDoor();
        else if (cmd == "CALL_NURSE") nurse.ShowNurse();
        else if (cmd == "TOGGLE_LIGHT") lightCtrl.Toggle();
        else if (cmd == "TOGGLE_BED") bed.Toggle();

        // ===== MOVEMENT =====
        else if (cmd == "MOVE_FORWARD") mover.MoveForward();
        else if (cmd == "MOVE_LEFT") mover.MoveLeft();
        else if (cmd == "MOVE_RIGHT") mover.MoveRight();
        else if (cmd == "STOP") mover.StopMove();
    }

    private void OnApplicationQuit()
    {
        server?.Stop();
        if (serverThread != null && serverThread.IsAlive)
            serverThread.Abort();
    }
}