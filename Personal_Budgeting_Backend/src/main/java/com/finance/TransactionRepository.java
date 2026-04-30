package com.finance;
import java.sql.*;
import java.util.ArrayList; 
import java.util.List;      

public class TransactionRepository {
    
    public boolean addTransaction(Transaction t) {
        String sql = "INSERT INTO transactions(user_id, amount, category, date) VALUES(?,?,?,?)";
        
        try (Connection conn = DatabaseManager.connect();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {
            
            pstmt.setInt(1, t.getUserId());
            pstmt.setDouble(2, t.getAmount());
            pstmt.setString(3, t.getCategory());
            pstmt.setString(4, t.getDate());
            
            pstmt.executeUpdate();
            return true;
        } catch (SQLException e) {
            System.out.println("Error adding transaction: " + e.getMessage());
            return false;
        }
    }

    public List<Transaction> getAllTransactions(int userId) {
        List<Transaction> transactions = new ArrayList<>();
        String sql = "SELECT * FROM transactions WHERE user_id = ?";
        
        try (Connection conn = DatabaseManager.connect();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {
            
            pstmt.setInt(1, userId);
            ResultSet rs = pstmt.executeQuery(); 
            
            while (rs.next()) {
                Transaction t = new Transaction(
                    rs.getInt("user_id"),
                    rs.getDouble("amount"),
                    rs.getString("category"),
                    rs.getString("date")
                );
                transactions.add(t); 
            }
        } catch (SQLException e) {
            System.out.println("Error fetching transactions: " + e.getMessage());
        }
        return transactions; 
    }
}