package com.example;

/** A tiny class with one seeded bug for the generic-repair integration test. */
public class Calc {

    /** BUG: subtracts instead of adding. The fix is to return a + b. */
    public int add(int a, int b) {
        return a - b;
    }

    public int subtract(int a, int b) {
        return a - b;
    }
}
