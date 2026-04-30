package com.finance;
import java.sql.*;

public class UserRepository {
    
    public boolean signUp(String name, String email, String password) {
        String sql = "INSERT INTO users(name, email, password) VALUES(?,?,?)";
        
        try (Connection conn = DatabaseManager.connect();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {
            
            pstmt.setString(1, name);
            pstmt.setString(2, email);
            pstmt.setString(3, password);
            
            pstmt.executeUpdate();
            return true;
        } catch (SQLException e) {
            System.out.println("Registration Error: " + e.getMessage());
            return false;
        }
    }
    public int login(String email, String password) {
    String sql = "SELECT id FROM users WHERE email = ? AND password = ?";
    
    try (Connection conn = DatabaseManager.connect();
         PreparedStatement pstmt = conn.prepareStatement(sql)) {
        
        pstmt.setString(1, email);
        pstmt.setString(2, password);
        
        ResultSet rs = pstmt.executeQuery();
        
        if (rs.next()) {
            return rs.getInt("id"); 
        }
    } catch (SQLException e) {
        System.out.println("Login Error: " + e.getMessage());
    }
    return -1; 
    }
}