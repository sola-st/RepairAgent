package com.example;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

public class CalcTest {

    @Test
    public void testAdd() {
        assertEquals(5, new Calc().add(2, 3));
    }

    @Test
    public void testSubtract() {
        assertEquals(1, new Calc().subtract(3, 2));
    }
}
