using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class PlayerMover : MonoBehaviour
{
    public float moveSpeed = 3f;
    public float turnSpeed = 40f;
    public float turnTimeout = 0.6f;

    CharacterController controller;
    SimpleFPS simpleFPS;

    bool isMoving = false;
    int turnDirection = 0;
    float lastTurnCommandTime = 0f;

    void Start()
    {
        controller = GetComponent<CharacterController>();
        simpleFPS = GetComponent<SimpleFPS>();
    }

    void Update()
    {
        if (!isMoving) return;

        if (turnDirection != 0 && Time.time - lastTurnCommandTime > turnTimeout)
        {
            turnDirection = 0;
        }

        Vector3 move = transform.forward;
        controller.Move(move * moveSpeed * Time.deltaTime);

        if (turnDirection != 0)
        {
            transform.Rotate(Vector3.up, turnDirection * turnSpeed * Time.deltaTime);
        }
    }

    public void MoveForward()
    {
        isMoving = true;
        turnDirection = 0;
        if (simpleFPS) simpleFPS.aiControlled = true;
    }

    public void MoveLeft()
    {
        isMoving = true;
        turnDirection = -1;
        lastTurnCommandTime = Time.time;
        if (simpleFPS) simpleFPS.aiControlled = true;
    }

    public void MoveRight()
    {
        isMoving = true;
        turnDirection = 1;
        lastTurnCommandTime = Time.time;
        if (simpleFPS) simpleFPS.aiControlled = true;
    }

    public void StopMove()
    {
        isMoving = false;
        turnDirection = 0;
        if (simpleFPS) simpleFPS.aiControlled = false;
    }
}